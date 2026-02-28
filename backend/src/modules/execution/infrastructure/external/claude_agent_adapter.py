"""基于 Claude Agent SDK 的 Agent 运行时实现。

SDK-First: 薄封装层，直接委托 claude_agent_sdk.query()，
仅做配置映射 + 异常转换。

依赖链: Python → claude-agent-sdk → Claude Code CLI (Node.js) → Bedrock Invoke API
"""

import asyncio
import ipaddress
import random
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from urllib.parse import urlparse

import structlog
from claude_agent_sdk import (
    ClaudeAgentOptions,
    McpSdkServerConfig,
    SdkMcpTool,
    create_sdk_mcp_server,
    query,
)
from claude_agent_sdk._errors import (
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    MessageParseError,
    ProcessError,
)

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

# CLI 连接重试: CLIConnectionError / CLIJSONDecodeError (pipe 中断) 自动重试
_CLI_MAX_RETRIES = 3
_CLI_BASE_DELAY_S = 0.5


def _cli_retry_delay(attempt: int) -> float:
    """指数退避 + jitter: attempt=1→~0.5s, 2→~1s, 3→~2s"""
    base: float = _CLI_BASE_DELAY_S * (2 ** (attempt - 1))
    jitter: float = random.uniform(0, base * 0.3)  # noqa: S311
    return base + jitter


def _is_retryable_cli_error(exc: BaseException) -> bool:
    """CLIConnectionError/CLIJSONDecodeError/MessageParseError 可重试, CLINotFoundError 不可重试。"""
    if isinstance(exc, CLINotFoundError):
        return False
    if isinstance(exc, (CLIConnectionError, CLIJSONDecodeError, MessageParseError)):
        return True
    if isinstance(exc, BaseExceptionGroup):
        return any(_is_retryable_cli_error(e) for e in exc.exceptions)
    return False


# SSRF 防护: 禁止访问的内部主机名
_BLOCKED_HOSTS = frozenset(
    {
        "169.254.169.254",
        "metadata.google.internal",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",  # noqa: S104
    },
)


def _validate_url(url: str) -> None:
    """验证 URL 安全性，防止 SSRF 攻击。

    Raises:
        ValueError: URL 不安全（内部地址、非 HTTP(S) 协议）
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        msg = "仅支持 HTTP/HTTPS 协议"
        raise ValueError(msg)
    hostname = parsed.hostname or ""
    if hostname in _BLOCKED_HOSTS:
        msg = f"禁止访问内部地址: {hostname}"
        raise ValueError(msg)
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        # hostname 不是 IP 地址, DNS 解析后再验证
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        msg = f"禁止访问内网地址: {hostname}"
        raise ValueError(msg)


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
        """同步执行 Agent, CLIConnectionError 自动重试。"""
        last_err: BaseException | None = None

        for attempt in range(_CLI_MAX_RETRIES + 1):
            if attempt > 0:
                logger.info("cli_connection_retry", attempt=attempt, max_retries=_CLI_MAX_RETRIES)
                await asyncio.sleep(_cli_retry_delay(attempt))

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
            except asyncio.CancelledError:
                raise
            except ProcessError as e:
                if e.stderr:
                    logger.warning("claude_agent_sdk_cli_stderr", stderr=e.stderr[:500], exit_code=e.exit_code)
                if content_parts:
                    logger.warning("claude_agent_sdk_process_exit1_ignored", exit_code=e.exit_code)
                else:
                    logger.exception(
                        "claude_agent_sdk_failed_no_content",
                        exit_code=e.exit_code,
                        stderr=str(e.stderr)[:200],
                    )
                    raise DomainError(message="Agent 服务暂时不可用, 请稍后重试", code="AGENT_SDK_ERROR") from e
            except BaseException as e:
                if _is_retryable_cli_error(e) and attempt < _CLI_MAX_RETRIES:
                    logger.warning("cli_connection_error_will_retry", attempt=attempt, error=str(e)[:200])
                    last_err = e
                    continue
                err_msg = str(e)
                if content_parts and "exit code 1" in err_msg:
                    logger.warning("claude_agent_sdk_plain_exit1_ignored", error=err_msg[:100])
                else:
                    logger.exception("Claude Agent SDK 调用失败", retries_exhausted=attempt >= _CLI_MAX_RETRIES)
                    raise DomainError(message="Agent 服务暂时不可用, 请稍后重试", code="AGENT_SDK_ERROR") from e

            return AgentResponseChunk(
                content="".join(content_parts),
                done=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

        raise DomainError(
            message="Agent 服务暂时不可用, 请稍后重试",
            code="AGENT_SDK_ERROR",
        ) from last_err

    async def execute_stream(self, request: AgentRequest) -> AsyncIterator[AgentResponseChunk]:
        """流式执行 Agent，逐条 yield 响应片段。"""
        options = self._build_options(request)
        return self._stream_messages(request.prompt, options)

    async def _stream_messages(
        self,
        prompt: str,
        options: ClaudeAgentOptions,
    ) -> AsyncIterator[AgentResponseChunk]:
        """内部流式消息生成器, CLIConnectionError 在未产出内容时自动重试。"""
        last_err: BaseException | None = None

        for attempt in range(_CLI_MAX_RETRIES + 1):
            if attempt > 0:
                logger.info("cli_connection_retry_stream", attempt=attempt)
                await asyncio.sleep(_cli_retry_delay(attempt))

            input_tokens = 0
            output_tokens = 0
            has_content = False

            try:
                async for message in query(prompt=prompt, options=options):
                    msg_content = extract_content(message)
                    if msg_content:
                        has_content = True
                        yield AgentResponseChunk(content=msg_content)
                    msg_input, msg_output = extract_usage(message)
                    input_tokens += msg_input
                    output_tokens += msg_output
            except DomainError:
                raise
            except asyncio.CancelledError:
                raise
            except ProcessError as e:
                if e.stderr:
                    logger.warning("claude_agent_sdk_cli_stderr_stream", stderr=e.stderr[:500], exit_code=e.exit_code)
                if not has_content:
                    logger.exception(
                        "claude_agent_sdk_failed_no_content_stream",
                        exit_code=e.exit_code,
                        stderr=str(e.stderr)[:200],
                    )
                    raise DomainError(message="Agent 服务暂时不可用, 请稍后重试", code="AGENT_SDK_ERROR") from e
                logger.warning("claude_agent_sdk_process_exit1_ignored", exit_code=e.exit_code)
            except BaseException as e:
                if _is_retryable_cli_error(e) and not has_content and attempt < _CLI_MAX_RETRIES:
                    logger.warning("cli_connection_error_will_retry_stream", attempt=attempt, error=str(e)[:200])
                    last_err = e
                    continue
                err_msg = str(e)
                if has_content and "exit code 1" in err_msg:
                    logger.warning("claude_agent_sdk_plain_exit1_stream_ignored", error=err_msg[:100])
                else:
                    logger.exception("Claude Agent SDK 流式调用失败")
                    raise DomainError(message="Agent 服务暂时不可用, 请稍后重试", code="AGENT_SDK_ERROR") from e

            yield AgentResponseChunk(
                done=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            return

        raise DomainError(
            message="Agent 服务暂时不可用, 请稍后重试",
            code="AGENT_SDK_ERROR",
        ) from last_err

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

        - tool_type == "mcp_server" -> 通过 AgentCore Gateway SSE 连接
        - tool_type == "api" 或 "function" -> 封装为 SDK 进程内 MCP Server
        """
        mcp_servers: dict[str, Any] = {}

        has_mcp_tools = any(t.tool_type == "mcp_server" for t in request.tools)

        # AgentCore Gateway MCP 配置 (需要有效 auth_token, 否则 CLI 连接 401 导致进程崩溃)
        if has_mcp_tools and request.gateway_url:
            if request.gateway_auth_token:
                mcp_servers["gateway"] = {
                    "type": "sse",
                    "url": request.gateway_url,
                    "requestInit": {
                        "headers": {"Authorization": f"Bearer {request.gateway_auth_token}"},
                    },
                }
            else:
                mcp_tool_names = [t.name for t in request.tools if t.tool_type == "mcp_server"]
                logger.warning(
                    "gateway_mcp_skipped_no_auth",
                    reason="gateway_auth_token 未配置, 跳过 gateway MCP 避免 CLI 401 崩溃",
                    skipped_tools=mcp_tool_names,
                )

        # API / Function 工具 -> SDK MCP Server
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

    def _build_platform_tools_config(self, tools: list[AgentTool]) -> McpSdkServerConfig:
        """将 API/Function 工具封装为 SDK 进程内 MCP Server。

        使用 claude_agent_sdk.create_sdk_mcp_server 创建进程内 MCP Server，
        每个 AgentTool 注册为 SdkMcpTool，handler 基于 tool.config 执行调用。
        """
        sdk_tools: list[SdkMcpTool[dict[str, Any]]] = []

        for t in tools:
            handler = self._create_tool_handler(t)
            sdk_tool = SdkMcpTool(
                name=t.name,
                description=t.description,
                input_schema=t.input_schema,
                handler=handler,
            )
            sdk_tools.append(sdk_tool)

        return create_sdk_mcp_server(
            name="platform-tools",
            tools=sdk_tools,
        )

    @staticmethod
    def _create_tool_handler(
        tool: AgentTool,
    ) -> Callable[[dict[str, Any]], Coroutine[object, object, dict[str, Any]]]:
        """为 API/Function 工具创建 handler 闭包。

        handler 根据 tool.config 中的配置（endpoint_url, method 等）执行调用，
        将结果封装为 MCP 工具响应格式返回。
        """
        config = tool.config

        async def _handler(args: dict[str, Any]) -> dict[str, Any]:
            # API 类型: 发起 HTTP 请求
            if tool.tool_type == "api" and config.get("endpoint_url"):
                return await ClaudeAgentAdapter._call_api_tool(config, args)
            # Function 或无 endpoint 的工具: 返回参数摘要
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"工具 '{tool.name}' 已调用, 参数: {args}",
                    },
                ],
            }

        return _handler

    @staticmethod
    async def _call_api_tool(
        config: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """通过 HTTP 调用 API 类型工具。"""
        import httpx

        url = config["endpoint_url"]
        _validate_url(url)
        method = config.get("method", "POST").upper()
        headers: dict[str, str] = {"Content-Type": "application/json"}

        # 认证头注入
        auth_type = config.get("auth_type", "")
        if auth_type == "api_key" and config.get("api_key"):
            headers["Authorization"] = f"Bearer {config['api_key']}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    resp = await client.get(url, params=args, headers=headers)
                else:
                    resp = await client.request(method, url, json=args, headers=headers)
                resp.raise_for_status()
                return {
                    "content": [{"type": "text", "text": resp.text}],
                }
        except httpx.HTTPError as e:
            logger.warning("API 工具调用失败", url=url, error=str(e))
            return {
                "content": [{"type": "text", "text": f"API 调用失败: {e}"}],
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
