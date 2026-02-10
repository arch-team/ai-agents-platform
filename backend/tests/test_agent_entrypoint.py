"""Agent 入口点单元测试。

测试 invoke() 函数的输入输出格式、payload 解析和 MCP 配置构建。
"""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.agent_entrypoint import _build_mcp_servers, invoke


class _AsyncIterFromList:
    """将列表包装为异步迭代器，用于模拟 query() 返回值。"""

    def __init__(self, items: list[Any]) -> None:
        self._items = items
        self._index = 0

    def __aiter__(self) -> AsyncIterator[Any]:
        return self  # type: ignore[return-value]

    async def __anext__(self) -> Any:
        if self._index >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._index]
        self._index += 1
        return item


def _mock_query(messages: list[Any]) -> MagicMock:
    """创建模拟的 query 函数，返回异步迭代器。"""
    mock = MagicMock()
    mock.return_value = _AsyncIterFromList(messages)
    return mock


@pytest.mark.unit
class TestBuildMcpServers:
    """测试 _build_mcp_servers 辅助函数。"""

    def test_with_gateway_url_returns_config(self):
        result = _build_mcp_servers("https://gateway.example.com/mcp")
        assert result == {"gateway": {"type": "sse", "url": "https://gateway.example.com/mcp"}}

    def test_with_empty_string_returns_empty_dict(self):
        result = _build_mcp_servers("")
        assert result == {}


@pytest.mark.unit
@pytest.mark.asyncio
class TestInvoke:
    """测试 AgentCore Runtime invoke 入口函数。"""

    async def test_basic_prompt_returns_content(self):
        """基本 prompt 调用，返回正确的响应结构。"""
        msg = MagicMock()
        msg.content = [MagicMock(text="你好，我是 AI 助手")]
        msg.usage = {"input_tokens": 100, "output_tokens": 50}
        msg.session_id = "sess-001"

        mock = _mock_query([msg])

        with patch("src.agent_entrypoint.query", mock):
            result = await invoke({"prompt": "你好"})

        assert result["content"] == "你好，我是 AI 助手"
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["session_id"] == "sess-001"

    async def test_empty_payload_uses_defaults(self):
        """空 payload 使用默认值，不抛异常。"""
        mock = _mock_query([])

        with patch("src.agent_entrypoint.query", mock):
            result = await invoke({})

        # 验证默认值传递
        call_kwargs = mock.call_args
        assert call_kwargs.kwargs["prompt"] == ""
        options = call_kwargs.kwargs["options"]
        assert options.system_prompt == ""
        assert options.max_turns == 20
        assert options.mcp_servers == {}
        assert options.allowed_tools == []
        assert options.cwd is None

        # 空响应返回默认结构
        assert result["content"] == ""
        assert result["input_tokens"] == 0
        assert result["output_tokens"] == 0
        assert result["session_id"] is None

    async def test_gateway_url_builds_mcp_config(self):
        """提供 gateway_url 时构建 MCP 配置。"""
        mock = _mock_query([])

        payload = {
            "prompt": "测试",
            "gateway_url": "https://gateway.example.com/mcp",
        }

        with patch("src.agent_entrypoint.query", mock):
            await invoke(payload)

        options = mock.call_args.kwargs["options"]
        assert options.mcp_servers == {"gateway": {"type": "sse", "url": "https://gateway.example.com/mcp"}}

    async def test_without_gateway_url_empty_mcp_config(self):
        """不提供 gateway_url 时 MCP 配置为空字典。"""
        mock = _mock_query([])

        with patch("src.agent_entrypoint.query", mock):
            await invoke({"prompt": "测试"})

        options = mock.call_args.kwargs["options"]
        assert options.mcp_servers == {}

    async def test_allowed_tools_passed_to_options(self):
        """allowed_tools 正确传递给 ClaudeAgentOptions。"""
        mock = _mock_query([])

        payload = {
            "prompt": "测试",
            "allowed_tools": ["mcp__gateway__tool1", "mcp__gateway__tool2"],
        }

        with patch("src.agent_entrypoint.query", mock):
            await invoke(payload)

        options = mock.call_args.kwargs["options"]
        assert options.allowed_tools == ["mcp__gateway__tool1", "mcp__gateway__tool2"]

    async def test_custom_max_turns(self):
        """自定义 max_turns 正确传递。"""
        mock = _mock_query([])

        with patch("src.agent_entrypoint.query", mock):
            await invoke({"prompt": "测试", "max_turns": 5})

        options = mock.call_args.kwargs["options"]
        assert options.max_turns == 5

    async def test_custom_cwd(self):
        """自定义 cwd 正确传递。"""
        mock = _mock_query([])

        with patch("src.agent_entrypoint.query", mock):
            await invoke({"prompt": "测试", "cwd": "/workspace"})

        options = mock.call_args.kwargs["options"]
        assert options.cwd == "/workspace"

    async def test_multiple_messages_concatenated(self):
        """多条消息的内容拼接。"""
        msg1 = MagicMock()
        msg1.content = [MagicMock(text="第一段")]
        msg1.usage = {"input_tokens": 50, "output_tokens": 20}
        msg1.session_id = "sess-001"

        msg2 = MagicMock()
        msg2.content = [MagicMock(text="第二段")]
        msg2.usage = {"input_tokens": 80, "output_tokens": 40}
        msg2.session_id = "sess-001"

        mock = _mock_query([msg1, msg2])

        with patch("src.agent_entrypoint.query", mock):
            result = await invoke({"prompt": "测试"})

        assert result["content"] == "第一段第二段"
        # usage 取最后一条消息的值
        assert result["input_tokens"] == 80
        assert result["output_tokens"] == 40

    async def test_string_content_block(self):
        """字符串类型的 content block 正确处理。"""
        msg = MagicMock()
        msg.content = "纯文本响应"
        msg.usage = None
        msg.session_id = None

        mock = _mock_query([msg])

        with patch("src.agent_entrypoint.query", mock):
            result = await invoke({"prompt": "测试"})

        assert result["content"] == "纯文本响应"

    async def test_system_prompt_passed_to_options(self):
        """system_prompt 正确传递给 ClaudeAgentOptions。"""
        mock = _mock_query([])

        payload = {
            "prompt": "你好",
            "system_prompt": "你是一个有帮助的助手",
        }

        with patch("src.agent_entrypoint.query", mock):
            await invoke(payload)

        options = mock.call_args.kwargs["options"]
        assert options.system_prompt == "你是一个有帮助的助手"

    async def test_permission_mode_is_bypass(self):
        """permission_mode 固定为 bypassPermissions。"""
        mock = _mock_query([])

        with patch("src.agent_entrypoint.query", mock):
            await invoke({"prompt": "测试"})

        options = mock.call_args.kwargs["options"]
        assert options.permission_mode == "bypassPermissions"
