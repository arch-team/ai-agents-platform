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
        "gateway_url": "AgentCore Gateway MCP 端点",
        "allowed_tools": ["mcp__gateway__*"],
        "max_turns": 20,
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

    async def execute_stream(
        self,
        request: AgentRequest,
    ) -> AsyncIterator[AgentResponseChunk]:
        """流式执行 Agent。

        当前 AgentCore Runtime invoke API 为同步调用,
        先获取完整结果再逐段 yield 模拟流式效果。
        后续可升级为真流式 (AgentCore Runtime 原生 streaming)。
        """
        chunk = await self.execute(request)

        # 将完整内容分段 yield 模拟流式
        content = chunk.content
        if content:
            yield AgentResponseChunk(content=content)

        yield AgentResponseChunk(
            done=True,
            input_tokens=chunk.input_tokens,
            output_tokens=chunk.output_tokens,
        )

    def _build_payload(self, request: AgentRequest) -> dict[str, Any]:
        """构建 agent_entrypoint.py 期望的 payload 格式。"""
        payload: dict[str, Any] = {
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "max_turns": request.max_turns,
        }

        if request.gateway_url:
            payload["gateway_url"] = request.gateway_url

        # 工具白名单
        allowed_tools: list[str] = []
        for tool in request.tools:
            if tool.tool_type == "mcp_server":
                allowed_tools.append(f"mcp__gateway__{tool.name}")
            elif tool.tool_type in ("api", "function"):
                allowed_tools.append(f"mcp__platform-tools__{tool.name}")
        if allowed_tools:
            payload["allowed_tools"] = allowed_tools

        return payload

    @staticmethod
    def _parse_response(response: dict[str, Any]) -> AgentResponseChunk:
        """解析 AgentCore Runtime 返回的响应。"""
        # invoke_agent_runtime 返回格式: {"body": ..., "statusCode": ...}
        body = response.get("body", response)

        # body 可能是 JSON 字符串或 dict
        if isinstance(body, str):
            body = json.loads(body)
        elif hasattr(body, "read"):
            body = json.loads(body.read())

        content = str(body.get("content", ""))
        input_tokens = int(body.get("input_tokens", 0))
        output_tokens = int(body.get("output_tokens", 0))

        return AgentResponseChunk(
            content=content,
            done=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
