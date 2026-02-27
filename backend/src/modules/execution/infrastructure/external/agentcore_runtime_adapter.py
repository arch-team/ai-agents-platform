"""基于 AgentCore Runtime API 的 Agent 运行时实现。

SDK-First: 薄封装层，通过 boto3 调用 bedrock-agent-runtime 的
invoke_inline_agent API，仅做配置映射 + 异常转换。

依赖链: Python → boto3 → Bedrock AgentCore Runtime API (invoke_inline_agent)
"""

import uuid
from collections.abc import AsyncIterator
from typing import Any, Protocol

import structlog

from src.modules.execution.application.interfaces import (
    AgentRequest,
    AgentResponseChunk,
    IAgentRuntime,
)
from src.shared.domain.constants import AGENT_DEFAULT_MODEL_ID
from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


class _AgentRuntimeClient(Protocol):
    """boto3 bedrock-agent-runtime client 最小协议。"""

    def invoke_inline_agent(self, **kwargs: Any) -> dict[str, Any]: ...  # noqa: ANN401


class AgentCoreRuntimeAdapter(IAgentRuntime):
    """基于 AgentCore Runtime API 的 Agent 运行时实现。

    通过 boto3 bedrock-agent-runtime 客户端调用 invoke_inline_agent，
    支持同步和流式响应。
    """

    def __init__(
        self,
        *,
        client: _AgentRuntimeClient,
        default_model_id: str = AGENT_DEFAULT_MODEL_ID,
    ) -> None:
        self._client = client
        self._default_model_id = default_model_id

    async def execute(self, request: AgentRequest) -> AgentResponseChunk:
        """同步执行 Agent，收集所有 chunk 后返回完整结果。"""
        try:
            response = self._client.invoke_inline_agent(
                **self._build_invoke_params(request),
            )
        except DomainError:
            raise
        except Exception as e:
            logger.exception("AgentCore Runtime API 调用失败")
            raise DomainError(
                message="Agent 服务暂时不可用, 请稍后重试",
                code="AGENTCORE_RUNTIME_ERROR",
            ) from e

        content_parts: list[str] = []
        for event in response.get("completion", []):
            chunk_data = event.get("chunk")
            if chunk_data and "bytes" in chunk_data:
                content_parts.append(chunk_data["bytes"].decode("utf-8"))

        return AgentResponseChunk(
            content="".join(content_parts),
            done=True,
        )

    async def execute_stream(  # type: ignore[override]
        self,
        request: AgentRequest,
    ) -> AsyncIterator[AgentResponseChunk]:
        """流式执行 Agent，逐 chunk yield 响应片段。"""
        try:
            response = self._client.invoke_inline_agent(
                **self._build_invoke_params(request),
            )
        except DomainError:
            raise
        except Exception as e:
            logger.exception("AgentCore Runtime API 流式调用失败")
            raise DomainError(
                message="Agent 服务暂时不可用, 请稍后重试",
                code="AGENTCORE_RUNTIME_ERROR",
            ) from e

        return self._stream_events(response)

    async def _stream_events(
        self,
        response: dict[str, Any],
    ) -> AsyncIterator[AgentResponseChunk]:
        """内部流式事件生成器。"""
        for event in response.get("completion", []):
            chunk_data = event.get("chunk")
            if chunk_data and "bytes" in chunk_data:
                yield AgentResponseChunk(
                    content=chunk_data["bytes"].decode("utf-8"),
                )

        yield AgentResponseChunk(done=True)

    _MIN_INSTRUCTION_LEN = 40

    def _build_invoke_params(self, request: AgentRequest) -> dict[str, Any]:
        """构建 invoke_inline_agent 请求参数。"""
        model_id = request.model_id or self._default_model_id
        instruction = request.system_prompt or "You are a helpful assistant."
        # invoke_inline_agent 要求 instruction 最少 40 字符
        if len(instruction) < self._MIN_INSTRUCTION_LEN:
            instruction = instruction.ljust(self._MIN_INSTRUCTION_LEN)

        params: dict[str, Any] = {
            "foundationModel": model_id,
            "inputText": request.prompt,
            "instruction": instruction,
            "enableTrace": False,
            # sessionId 是必填参数, 用于管理对话状态
            "sessionId": uuid.uuid4().hex[:12],
        }

        return params
