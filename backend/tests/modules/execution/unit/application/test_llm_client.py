"""ILLMClient 接口和数据结构测试。"""

import pytest

from src.modules.execution.application.interfaces.llm_client import (
    ILLMClient,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
)


@pytest.mark.unit
class TestLLMMessage:
    def test_create_user_message(self) -> None:
        msg = LLMMessage(role="user", content="你好")
        assert msg.role == "user"
        assert msg.content == "你好"

    def test_create_assistant_message(self) -> None:
        msg = LLMMessage(role="assistant", content="你好，有什么可以帮助你？")
        assert msg.role == "assistant"
        assert msg.content == "你好，有什么可以帮助你？"


@pytest.mark.unit
class TestLLMResponse:
    def test_create_response(self) -> None:
        resp = LLMResponse(content="回复内容", input_tokens=10, output_tokens=20)
        assert resp.content == "回复内容"
        assert resp.input_tokens == 10
        assert resp.output_tokens == 20


@pytest.mark.unit
class TestLLMStreamChunk:
    def test_default_values(self) -> None:
        chunk = LLMStreamChunk()
        assert chunk.content == ""
        assert chunk.done is False
        assert chunk.input_tokens == 0
        assert chunk.output_tokens == 0

    def test_content_chunk(self) -> None:
        chunk = LLMStreamChunk(content="部分内容")
        assert chunk.content == "部分内容"
        assert chunk.done is False

    def test_done_chunk_with_tokens(self) -> None:
        chunk = LLMStreamChunk(done=True, input_tokens=50, output_tokens=100)
        assert chunk.done is True
        assert chunk.input_tokens == 50
        assert chunk.output_tokens == 100


@pytest.mark.unit
class TestILLMClient:
    def test_is_abstract_class(self) -> None:
        assert ILLMClient.__abstractmethods__ == frozenset(
            {"invoke", "invoke_stream"},
        )

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            ILLMClient()  # type: ignore[abstract]
