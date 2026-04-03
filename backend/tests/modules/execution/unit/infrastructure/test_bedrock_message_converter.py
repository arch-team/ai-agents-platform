"""Bedrock 消息格式转换器测试。

覆盖 src/modules/execution/infrastructure/external/bedrock_message_converter.py
中的所有转换函数。
"""

import pytest

from src.modules.execution.application.interfaces.llm_client import (
    LLMMessage,
    LLMStreamChunk,
)
from src.modules.execution.infrastructure.external.bedrock_message_converter import (
    build_converse_kwargs,
    iter_stream_chunks,
    parse_converse_response,
    to_bedrock_messages,
)


@pytest.mark.unit
class TestToBedRockMessages:
    """to_bedrock_messages 测试。"""

    def test_converts_single_message(self):
        """单条消息正确转换为 Bedrock 格式。"""
        messages = [LLMMessage(role="user", content="你好")]
        result = to_bedrock_messages(messages)

        assert result == [{"role": "user", "content": [{"text": "你好"}]}]

    def test_converts_multiple_messages(self):
        """多条消息正确转换。"""
        messages = [
            LLMMessage(role="user", content="你好"),
            LLMMessage(role="assistant", content="你好！有什么能帮你的？"),
        ]
        result = to_bedrock_messages(messages)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_empty_list_returns_empty(self):
        """空列表返回空列表。"""
        assert to_bedrock_messages([]) == []


@pytest.mark.unit
class TestBuildConverseKwargs:
    """build_converse_kwargs 测试。"""

    def test_basic_kwargs(self):
        """构建基本参数。"""
        messages = [{"role": "user", "content": [{"text": "hello"}]}]
        result = build_converse_kwargs(
            model_id="claude-3",
            messages=messages,
            system_prompt="",
            temperature=0.7,
            max_tokens=1024,
            top_p=0.9,
            stop_sequences=(),
        )

        assert result["modelId"] == "claude-3"
        assert result["messages"] == messages
        assert "system" not in result
        assert result["inferenceConfig"]["temperature"] == 0.7
        assert result["inferenceConfig"]["maxTokens"] == 1024
        assert "stopSequences" not in result["inferenceConfig"]

    def test_with_system_prompt(self):
        """包含 system prompt 时添加 system 字段。"""
        result = build_converse_kwargs(
            model_id="claude-3",
            messages=[],
            system_prompt="你是助手",
            temperature=0.5,
            max_tokens=512,
            top_p=0.95,
            stop_sequences=(),
        )

        assert result["system"] == [{"text": "你是助手"}]

    def test_with_stop_sequences(self):
        """包含 stop_sequences 时添加到 inferenceConfig。"""
        result = build_converse_kwargs(
            model_id="claude-3",
            messages=[],
            system_prompt="",
            temperature=0.5,
            max_tokens=512,
            top_p=0.95,
            stop_sequences=("\n\nHuman:", "\n\nAssistant:"),
        )

        assert result["inferenceConfig"]["stopSequences"] == ["\n\nHuman:", "\n\nAssistant:"]


@pytest.mark.unit
class TestParseConverseResponse:
    """parse_converse_response 测试。"""

    def test_parses_standard_response(self):
        """解析标准 Bedrock Converse 响应。"""
        response = {
            "output": {
                "message": {
                    "content": [{"text": "你好！"}],
                },
            },
            "usage": {
                "inputTokens": 10,
                "outputTokens": 20,
            },
        }
        result = parse_converse_response(response)

        assert result.content == "你好！"
        assert result.input_tokens == 10
        assert result.output_tokens == 20

    def test_parses_multi_block_content(self):
        """解析多 block 内容并拼接。"""
        response = {
            "output": {
                "message": {
                    "content": [{"text": "第一段"}, {"text": "第二段"}],
                },
            },
            "usage": {},
        }
        result = parse_converse_response(response)

        assert result.content == "第一段第二段"

    def test_handles_empty_response(self):
        """空响应时返回默认值。"""
        result = parse_converse_response({})

        assert result.content == ""
        assert result.input_tokens == 0
        assert result.output_tokens == 0

    def test_ignores_non_text_blocks(self):
        """忽略非 text 类型的 block。"""
        response = {
            "output": {
                "message": {
                    "content": [{"image": "data"}, {"text": "有效文本"}],
                },
            },
            "usage": {"inputTokens": 5, "outputTokens": 10},
        }
        result = parse_converse_response(response)

        assert result.content == "有效文本"


@pytest.mark.unit
class TestIterStreamChunks:
    """iter_stream_chunks 测试。"""

    @pytest.mark.anyio
    async def test_yields_content_chunks(self):
        """正确 yield 内容片段。"""
        stream = [
            {"contentBlockDelta": {"delta": {"text": "你"}}},
            {"contentBlockDelta": {"delta": {"text": "好"}}},
            {"metadata": {"usage": {"inputTokens": 10, "outputTokens": 5}}},
        ]

        chunks: list[LLMStreamChunk] = []
        async for chunk in iter_stream_chunks(stream):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].content == "你"
        assert chunks[1].content == "好"
        # 最后一个 chunk 带 done 标志和 token 统计
        assert chunks[2].done is True
        assert chunks[2].input_tokens == 10
        assert chunks[2].output_tokens == 5

    @pytest.mark.anyio
    async def test_yields_done_chunk_without_content(self):
        """只有 metadata 时也 yield done chunk。"""
        stream = [
            {"metadata": {"usage": {"inputTokens": 0, "outputTokens": 0}}},
        ]

        chunks: list[LLMStreamChunk] = []
        async for chunk in iter_stream_chunks(stream):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].done is True

    @pytest.mark.anyio
    async def test_empty_stream(self):
        """空流仍 yield 一个 done chunk。"""
        chunks: list[LLMStreamChunk] = []
        async for chunk in iter_stream_chunks([]):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].done is True
        assert chunks[0].input_tokens == 0
        assert chunks[0].output_tokens == 0

    @pytest.mark.anyio
    async def test_skips_empty_text_delta(self):
        """空 text delta 不 yield 内容 chunk。"""
        stream = [
            {"contentBlockDelta": {"delta": {"text": ""}}},
            {"contentBlockDelta": {"delta": {}}},
            {"metadata": {}},
        ]

        chunks: list[LLMStreamChunk] = []
        async for chunk in iter_stream_chunks(stream):
            chunks.append(chunk)

        # 只有最后的 done chunk
        assert len(chunks) == 1
        assert chunks[0].done is True
