"""Bedrock Converse API 薄封装 — async 包装 + 异常转换。"""

import asyncio
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Protocol

import structlog

from src.modules.execution.application.interfaces import (
    ILLMClient,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
)
from src.modules.execution.infrastructure.external.bedrock_message_converter import (
    build_converse_kwargs,
    iter_stream_chunks,
    parse_converse_response,
    to_bedrock_messages,
)
from src.shared.domain.constants import (
    AGENT_DEFAULT_MAX_TOKENS,
    AGENT_DEFAULT_TEMPERATURE,
    AGENT_DEFAULT_TOP_P,
)
from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


class _BedrockRuntimeClient(Protocol):
    def converse(self, **kwargs: Any) -> dict[str, Any]: ...  # noqa: ANN401
    def converse_stream(self, **kwargs: Any) -> dict[str, Any]: ...  # noqa: ANN401


class BedrockLLMClient(ILLMClient):
    """基于 Amazon Bedrock Converse API 的 LLM 客户端。"""

    def __init__(self, client: _BedrockRuntimeClient, *, max_workers: int = 50) -> None:
        self._client = client
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="bedrock")

    async def invoke(  # noqa: D102
        self,
        model_id: str,
        messages: list[LLMMessage],
        *,
        system_prompt: str = "",
        temperature: float = AGENT_DEFAULT_TEMPERATURE,
        max_tokens: int = AGENT_DEFAULT_MAX_TOKENS,
        top_p: float = AGENT_DEFAULT_TOP_P,
        stop_sequences: tuple[str, ...] = (),
    ) -> LLMResponse:
        kwargs = build_converse_kwargs(
            model_id,
            to_bedrock_messages(messages),
            system_prompt,
            temperature,
            max_tokens,
            top_p,
            stop_sequences,
        )
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(self._executor, lambda: self._client.converse(**kwargs))
        except Exception as e:
            logger.exception("Bedrock Converse API 调用失败")
            raise DomainError(message="LLM 服务暂时不可用, 请稍后重试", code="BEDROCK_API_ERROR") from e
        return parse_converse_response(response)

    async def invoke_stream(  # noqa: D102
        self,
        model_id: str,
        messages: list[LLMMessage],
        *,
        system_prompt: str = "",
        temperature: float = AGENT_DEFAULT_TEMPERATURE,
        max_tokens: int = AGENT_DEFAULT_MAX_TOKENS,
        top_p: float = AGENT_DEFAULT_TOP_P,
        stop_sequences: tuple[str, ...] = (),
    ) -> AsyncIterator[LLMStreamChunk]:
        kwargs = build_converse_kwargs(
            model_id,
            to_bedrock_messages(messages),
            system_prompt,
            temperature,
            max_tokens,
            top_p,
            stop_sequences,
        )
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(self._executor, lambda: self._client.converse_stream(**kwargs))
        except Exception as e:
            logger.exception("Bedrock ConverseStream API 调用失败")
            raise DomainError(message="LLM 服务暂时不可用, 请稍后重试", code="BEDROCK_API_ERROR") from e
        return iter_stream_chunks(response.get("stream", []))
