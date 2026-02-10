"""SDK 消息解析工具测试。"""

from types import SimpleNamespace

import pytest

from src.modules.execution.infrastructure.external.sdk_message_utils import (
    extract_content,
    extract_usage,
)


@pytest.mark.unit
class TestExtractContent:
    def test_dict_text_type(self) -> None:
        msg = {"type": "text", "content": "hello"}
        assert extract_content(msg) == "hello"

    def test_dict_content_key(self) -> None:
        msg = {"content": "hello"}
        assert extract_content(msg) == "hello"

    def test_dict_no_content(self) -> None:
        msg = {"type": "other"}
        assert extract_content(msg) == ""

    def test_object_string_content(self) -> None:
        msg = SimpleNamespace(content="hello")
        assert extract_content(msg) == "hello"

    def test_object_list_content_with_text_blocks(self) -> None:
        block1 = SimpleNamespace(text="hello ")
        block2 = SimpleNamespace(text="world")
        msg = SimpleNamespace(content=[block1, block2])
        assert extract_content(msg) == "hello world"

    def test_object_list_content_with_string_blocks(self) -> None:
        msg = SimpleNamespace(content=["hello ", "world"])
        assert extract_content(msg) == "hello world"

    def test_plain_string(self) -> None:
        assert extract_content("hello") == "hello"

    def test_none_returns_empty(self) -> None:
        assert extract_content(None) == ""

    def test_int_returns_empty(self) -> None:
        assert extract_content(42) == ""


@pytest.mark.unit
class TestExtractUsage:
    def test_dict_format(self) -> None:
        msg = {"usage": {"input_tokens": 10, "output_tokens": 20}}
        assert extract_usage(msg) == (10, 20)

    def test_dict_no_usage(self) -> None:
        msg = {"content": "hello"}
        assert extract_usage(msg) == (0, 0)

    def test_object_dict_usage(self) -> None:
        msg = SimpleNamespace(usage={"input_tokens": 5, "output_tokens": 15})
        assert extract_usage(msg) == (5, 15)

    def test_object_attribute_usage(self) -> None:
        usage = SimpleNamespace(input_tokens=8, output_tokens=12)
        msg = SimpleNamespace(usage=usage)
        assert extract_usage(msg) == (8, 12)

    def test_none_usage(self) -> None:
        msg = SimpleNamespace(usage=None)
        assert extract_usage(msg) == (0, 0)

    def test_no_usage_attribute(self) -> None:
        msg = SimpleNamespace(content="hello")
        assert extract_usage(msg) == (0, 0)

    def test_plain_dict(self) -> None:
        assert extract_usage({}) == (0, 0)
