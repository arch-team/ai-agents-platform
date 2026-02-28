"""基于 AgentCore Runtime 的 Agent 运行时实现。

SDK-First: 薄封装层，通过 bedrock-agentcore SDK 调用已部署到
AgentCore Runtime 的 Agent 应用 (agent_entrypoint.py)。

架构:
  ECS (Web API) → invoke_agent_runtime() → AgentCore Runtime 容器
                                            └── agent_entrypoint.py
                                                └── claude_agent_sdk.query()
                                                    └── bundled CLI → Bedrock API

Agent 执行在 AgentCore Runtime 独立容器中，与 ECS Web API 资源隔离。
"""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any, Protocol

import structlog

from src.modules.execution.application.interfaces import (
    AgentRequest,
    AgentResponseChunk,
    IAgentRuntime,
)
from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


class _AgentCoreClient(Protocol):
    """boto3 bedrock-agentcore client 最小协议。"""

    def invoke_agent_runtime(self, **kwargs: Any) -> dict[str, Any]: ...  # noqa: ANN401


class AgentCoreRuntimeAdapter(IAgentRuntime):
    """基于 AgentCore Runtime 的 Agent 运行时实现。

    通过 bedrock-agentcore SDK 的 invoke_agent_runtime API
    调用已部署在 AgentCore Runtime 上的 Agent 应用。

    Agent 应用 (agent_entrypoint.py) 接收 payload 格式:
    {
        "prompt": "用户消息",
        "system_prompt": "系统提示词",
        "model_id": "claude-sonnet-4-20250514",
        "gateway_url": "AgentCore Gateway MCP 端点",
        "allowed_tools": ["mcp__gateway__*"],
        "max_turns": 20,
        "cwd": "/workspace",
        "enable_teams": false,
        "memory_id": "agentcore-memory-id",
    }

    响应格式:
    {
        "content": "Agent 回复内容",
        "input_tokens": 100,
        "output_tokens": 200,
    }
    """

    def __init__(
        self,
        *,
        client: _AgentCoreClient,
        runtime_arn: str,
    ) -> None:
        self._client = client
        self._runtime_arn = runtime_arn

    async def execute(self, request: AgentRequest) -> AgentResponseChunk:
        """同步执行 Agent (阻塞式调用 AgentCore Runtime)。"""
        payload = self._build_payload(request)

        try:
            response = await asyncio.to_thread(
                self._client.invoke_agent_runtime,
                agentRuntimeArn=self._runtime_arn,
                payload=json.dumps(payload),
            )
        except DomainError:
            raise
        except Exception as e:
            logger.exception("agentcore_runtime_invoke_failed", runtime_arn=self._runtime_arn)
            raise DomainError(
                message="Agent 服务暂时不可用, 请稍后重试",
                code="AGENTCORE_RUNTIME_ERROR",
            ) from e

        return self._parse_response(response)

    async def execute_stream(self, request: AgentRequest) -> AsyncIterator[AgentResponseChunk]:
        """流式执行 Agent。

        当前 AgentCore Runtime invoke API 为同步调用,
        先获取完整结果再逐段 yield 模拟流式效果。
        后续可升级为真流式 (AgentCore Runtime 原生 streaming)。
        """
        return self._generate_stream(request)

    async def _generate_stream(self, request: AgentRequest) -> AsyncIterator[AgentResponseChunk]:
        """内部流式生成器: 同步调用后分段 yield。"""
        chunk = await self.execute(request)

        content = chunk.content
        if content:
            yield AgentResponseChunk(content=content)

        yield AgentResponseChunk(
            done=True,
            input_tokens=chunk.input_tokens,
            output_tokens=chunk.output_tokens,
        )

    def _build_payload(self, request: AgentRequest) -> dict[str, Any]:
        """构建 agent_entrypoint.py 期望的 payload 格式。

        与 ClaudeAgentAdapter._build_options() 参数集保持对齐:
        prompt, system_prompt, model_id, max_turns, cwd, gateway_url,
        allowed_tools, enable_teams, memory_id。
        """
        payload: dict[str, Any] = {
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "max_turns": request.max_turns,
        }

        if request.model_id:
            payload["model_id"] = request.model_id
        if request.gateway_url:
            payload["gateway_url"] = request.gateway_url
        if request.cwd:
            payload["cwd"] = request.cwd
        if request.enable_teams:
            payload["enable_teams"] = True
        if request.memory_id:
            payload["memory_id"] = request.memory_id

        # 工具白名单
        allowed_tools: list[str] = []
        for tool in request.tools:
            if tool.tool_type == "mcp_server":
                allowed_tools.append(f"mcp__gateway__{tool.name}")
            elif tool.tool_type in ("api", "function"):
                allowed_tools.append(f"mcp__platform-tools__{tool.name}")
        # Memory 工具白名单 (与 ClaudeAgentAdapter 对齐)
        if request.memory_id:
            allowed_tools.append("mcp__memory__save_memory")
            allowed_tools.append("mcp__memory__recall_memory")
        if allowed_tools:
            payload["allowed_tools"] = allowed_tools

        return payload

    @staticmethod
    def _parse_response(response: dict[str, Any]) -> AgentResponseChunk:
        """解析 AgentCore Runtime 返回的响应。

        bedrock-agentcore SDK invoke_agent_runtime 返回格式:
        {"response": StreamingBody, "statusCode": 200, "runtimeSessionId": "...", ...}
        StreamingBody 内容: {"content": "...", "input_tokens": N, "output_tokens": N}
        """
        # SDK 返回 "response" (StreamingBody) 或旧版 "body"
        body = response.get("response") or response.get("body") or response

        # StreamingBody → bytes → JSON
        if hasattr(body, "read"):
            body = json.loads(body.read())
        elif isinstance(body, (bytes, bytearray)) or isinstance(body, str):
            body = json.loads(body)

        content = str(body.get("content", ""))
        input_tokens = int(body.get("input_tokens", 0))
        output_tokens = int(body.get("output_tokens", 0))

        return AgentResponseChunk(
            content=content,
            done=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
