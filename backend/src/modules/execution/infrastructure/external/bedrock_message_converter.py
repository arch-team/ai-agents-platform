"""Bedrock Converse API 消息格式转换与参数构建。

BedrockLLMClient 的辅助模块，负责：
- LLMMessage → Bedrock 格式转换
- Bedrock 响应 → LLMResponse/LLMStreamChunk 转换
- Converse API 调用参数构建
"""

from collections.abc import AsyncIterator
from typing import Any

from src.modules.execution.application.interfaces import (
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
)


def to_bedrock_messages(messages: list[LLMMessage]) -> list[dict[str, Any]]:
    """LLMMessage 列表 → Bedrock Converse API 消息格式。"""
    return [{"role": m.role, "content": [{"text": m.content}]} for m in messages]


def build_converse_kwargs(
    model_id: str,
    messages: list[dict[str, Any]],
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    stop_sequences: tuple[str, ...],
) -> dict[str, Any]:
    """构建 Bedrock Converse / ConverseStream 调用参数。"""
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


def parse_converse_response(response: dict[str, Any]) -> LLMResponse:
    """Bedrock Converse 响应 → LLMResponse。"""
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


async def iter_stream_chunks(stream: Any) -> AsyncIterator[LLMStreamChunk]:  # noqa: ANN401
    """Bedrock ConverseStream 事件流 → LLMStreamChunk 异步迭代器。"""
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
