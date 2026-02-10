"""Bedrock ConverseStream API 薄封装。

SDK-First: < 100 行，暴露原生类型，
仅做 async 包装 + 异常转换。
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any, Protocol

import structlog

from src.modules.execution.application.interfaces import (
    ILLMClient,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
)
from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


class _BedrockRuntimeClient(Protocol):
    """boto3 bedrock-runtime client 最小协议。"""

    def converse(self, **kwargs: Any) -> dict[str, Any]: ...  # noqa: ANN401
    def converse_stream(self, **kwargs: Any) -> dict[str, Any]: ...  # noqa: ANN401


class BedrockLLMClient(ILLMClient):
    """基于 Amazon Bedrock Converse API 的 LLM 客户端。"""

    def __init__(self, client: _BedrockRuntimeClient) -> None:
        """初始化。client 是 boto3 bedrock-runtime client。"""
        self._client = client

    async def invoke(
        self,
        model_id: str,
        messages: list[LLMMessage],
        *,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 1.0,
        stop_sequences: tuple[str, ...] = (),
    ) -> LLMResponse:
        """同步调用 Bedrock Converse API。"""
        bedrock_messages = self._to_bedrock_messages(messages)
        kwargs = self._build_kwargs(
            model_id,
            bedrock_messages,
            system_prompt,
            temperature,
            max_tokens,
            top_p,
            stop_sequences,
        )
        try:
            response = await asyncio.to_thread(self._client.converse, **kwargs)
        except Exception as e:
            # 日志记录完整异常, 但不向用户暴露内部错误信息
            logger.exception("Bedrock Converse API 调用失败")
            raise DomainError(
                message="LLM 服务暂时不可用, 请稍后重试",
                code="BEDROCK_API_ERROR",
            ) from e

        output = response.get("output", {}).get("message", {})
        content = ""
        for block in output.get("content", []):
            if "text" in block:
                content += block["text"]

        usage = response.get("usage", {})
        return LLMResponse(
            content=content,
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
        )

    async def invoke_stream(
        self,
        model_id: str,
        messages: list[LLMMessage],
        *,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 1.0,
        stop_sequences: tuple[str, ...] = (),
    ) -> AsyncIterator[LLMStreamChunk]:
        """流式调用 Bedrock ConverseStream API。"""
        bedrock_messages = self._to_bedrock_messages(messages)
        kwargs = self._build_kwargs(
            model_id,
            bedrock_messages,
            system_prompt,
            temperature,
            max_tokens,
            top_p,
            stop_sequences,
        )
        try:
            response = await asyncio.to_thread(self._client.converse_stream, **kwargs)
        except Exception as e:
            logger.exception("Bedrock ConverseStream API 调用失败")
            raise DomainError(
                message="LLM 服务暂时不可用, 请稍后重试",
                code="BEDROCK_API_ERROR",
            ) from e

        stream = response.get("stream", [])

        async def _generate() -> AsyncIterator[LLMStreamChunk]:
            input_tokens = 0
            output_tokens = 0
            for event in stream:
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"].get("delta", {})
                    text = delta.get("text", "")
                    if text:
                        yield LLMStreamChunk(content=text)
                elif "metadata" in event:
                    usage = event["metadata"].get("usage", {})
                    input_tokens = usage.get("inputTokens", 0)
                    output_tokens = usage.get("outputTokens", 0)
            yield LLMStreamChunk(
                done=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

        return _generate()

    @staticmethod
    def _to_bedrock_messages(messages: list[LLMMessage]) -> list[dict[str, Any]]:
        return [{"role": m.role, "content": [{"text": m.content}]} for m in messages]

    @staticmethod
    def _build_kwargs(
        model_id: str,
        messages: list[dict[str, Any]],
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        stop_sequences: tuple[str, ...],
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"modelId": model_id, "messages": messages}
        if system_prompt:
            kwargs["system"] = [{"text": system_prompt}]
        inference_config: dict[str, Any] = {
            "temperature": temperature,
            "maxTokens": max_tokens,
            "topP": top_p,
        }
        if stop_sequences:
            inference_config["stopSequences"] = list(stop_sequences)
        kwargs["inferenceConfig"] = inference_config
        return kwargs
