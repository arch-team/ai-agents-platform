"""基于 Claude Agent SDK 的 Agent 运行时实现。

SDK-First: 薄封装层，直接委托 claude_agent_sdk.query()，
仅做配置映射 + 异常转换。

依赖链: Python → claude-agent-sdk → Claude Code CLI (Node.js) → Bedrock Invoke API
"""

from collections.abc import AsyncIterator
from typing import Any

import structlog
from claude_agent_sdk import ClaudeAgentOptions, query

from src.modules.execution.application.interfaces import (
    AgentRequest,
    AgentResponseChunk,
    AgentTool,
    IAgentRuntime,
)
from src.modules.execution.infrastructure.external.memory_mcp_server import (
    MemoryMcpConfig,
    build_memory_mcp_server_config,
)
from src.modules.execution.infrastructure.external.sdk_message_utils import (
    extract_content,
    extract_usage,
)
from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


class ClaudeAgentAdapter(IAgentRuntime):
    """基于 Claude Agent SDK 的 Agent 运行时实现。

    通过 claude_agent_sdk.query() 执行 Agent Loop，
    支持 MCP Server 工具调用和流式响应。
    """

    def __init__(
        self,
        *,
        memory_id: str = "",
        region: str = "us-east-1",
    ) -> None:
        self._memory_id = memory_id
        self._region = region

    async def execute(self, request: AgentRequest) -> AgentResponseChunk:
        """同步执行 Agent，收集所有消息后返回完整结果。"""
        options = self._build_options(request)
        content_parts: list[str] = []
        input_tokens = 0
        output_tokens = 0

        try:
            async for message in query(prompt=request.prompt, options=options):
                msg_content = extract_content(message)
                if msg_content:
                    content_parts.append(msg_content)
                msg_input, msg_output = extract_usage(message)
                input_tokens += msg_input
                output_tokens += msg_output
        except DomainError:
            raise
        except Exception as e:
            logger.exception("Claude Agent SDK 调用失败")
            raise DomainError(
                message="Agent 服务暂时不可用, 请稍后重试",
                code="AGENT_SDK_ERROR",
            ) from e

        return AgentResponseChunk(
            content="".join(content_parts),
            done=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    async def execute_stream(  # type: ignore[override]
        self,
        request: AgentRequest,
    ) -> AsyncIterator[AgentResponseChunk]:
        """流式执行 Agent，逐条 yield 响应片段。"""
        options = self._build_options(request)
        return self._stream_messages(request.prompt, options)

    async def _stream_messages(
        self,
        prompt: str,
        options: ClaudeAgentOptions,
    ) -> AsyncIterator[AgentResponseChunk]:
        """内部流式消息生成器。"""
        input_tokens = 0
        output_tokens = 0

        try:
            async for message in query(prompt=prompt, options=options):
                msg_content = extract_content(message)
                if msg_content:
                    yield AgentResponseChunk(content=msg_content)
                msg_input, msg_output = extract_usage(message)
                input_tokens += msg_input
                output_tokens += msg_output
        except DomainError:
            raise
        except Exception as e:
            logger.exception("Claude Agent SDK 流式调用失败")
            raise DomainError(
                message="Agent 服务暂时不可用, 请稍后重试",
                code="AGENT_SDK_ERROR",
            ) from e

        yield AgentResponseChunk(
            done=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def _build_options(self, request: AgentRequest) -> ClaudeAgentOptions:
        """构建 Claude Agent SDK 配置。"""
        kwargs: dict[str, Any] = {}

        if request.system_prompt:
            kwargs["system_prompt"] = request.system_prompt
        if request.model_id:
            kwargs["model"] = request.model_id
        if request.max_turns:
            kwargs["max_turns"] = request.max_turns
        if request.cwd:
            kwargs["cwd"] = request.cwd

        # MCP 服务器配置
        mcp_servers = self._build_mcp_config(request)
        if mcp_servers:
            kwargs["mcp_servers"] = mcp_servers

        # 工具白名单
        allowed_tools = self._build_allowed_tools(request)
        if allowed_tools:
            kwargs["allowed_tools"] = allowed_tools

        # 权限模式: Agent 自动化场景统一 bypassPermissions (与 agent_entrypoint 一致)
        kwargs["permission_mode"] = "bypassPermissions"

        # Agent Teams: 注入环境变量启用团队协作能力
        if request.enable_teams:
            env = kwargs.get("env", {})
            env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
            kwargs["env"] = env
            # 团队模式默认提升 max_turns
            if not request.max_turns or request.max_turns <= 20:
                kwargs["max_turns"] = 200

        return ClaudeAgentOptions(**kwargs)

    def _build_mcp_config(self, request: AgentRequest) -> dict[str, Any]:
        """构建 MCP 服务器配置。

        - tool_type == "mcp_server" → 通过 AgentCore Gateway SSE 连接
        - tool_type == "api" 或 "function" → TODO: 封装为 SDK MCP Server
        """
        mcp_servers: dict[str, Any] = {}

        has_mcp_tools = any(t.tool_type == "mcp_server" for t in request.tools)

        # AgentCore Gateway MCP 配置
        if has_mcp_tools and request.gateway_url:
            mcp_servers["gateway"] = {
                "type": "sse",
                "url": request.gateway_url,
            }

        # API / Function 工具 → SDK MCP Server
        non_mcp_tools = [t for t in request.tools if t.tool_type in ("api", "function")]
        if non_mcp_tools:
            mcp_servers["platform-tools"] = self._build_platform_tools_config(non_mcp_tools)

        # Memory MCP 配置 (可选)
        if self._memory_id:
            memory_config = build_memory_mcp_server_config(
                MemoryMcpConfig(memory_id=self._memory_id, region=self._region),
            )
            if memory_config:
                mcp_servers["memory"] = memory_config

        return mcp_servers

    def _build_platform_tools_config(self, tools: list[AgentTool]) -> dict[str, Any]:
        """将 API/Function 工具封装为 platform-tools MCP 配置。

        TODO: 当 claude_agent_sdk 提供 create_sdk_mcp_server 时替换为正式实现。
        当前使用 stdio 类型占位，工具信息通过 env 传递。
        """
        tool_definitions = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "config": t.config,
            }
            for t in tools
        ]

        return {
            "type": "stdio",
            "command": "platform-tools-server",
            "env": {"TOOL_DEFINITIONS": str(tool_definitions)},
        }

    def _build_allowed_tools(self, request: AgentRequest) -> list[str]:
        """构建工具白名单。"""
        allowed: list[str] = []

        for tool in request.tools:
            if tool.tool_type == "mcp_server":
                # MCP Server 工具: mcp__gateway__{tool_name}
                allowed.append(f"mcp__gateway__{tool.name}")
            elif tool.tool_type in ("api", "function"):
                # Platform 工具: mcp__platform-tools__{tool_name}
                allowed.append(f"mcp__platform-tools__{tool.name}")

        # Memory 工具白名单 (可选)
        if self._memory_id:
            allowed.append("mcp__memory__save_memory")
            allowed.append("mcp__memory__recall_memory")

        return allowed

    # SDK 消息解析已抽取到 sdk_message_utils 模块 (extract_content, extract_usage)
