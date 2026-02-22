"""集成测试: agent_entrypoint.py Gateway URL → ClaudeAgentOptions 传递。

验证 _build_mcp_servers 辅助函数和 invoke 中 gateway_url 到 mcp_servers 的映射。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, patch

import pytest

from src.agent_entrypoint import _build_mcp_servers


if TYPE_CHECKING:
    from collections.abc import AsyncIterator


pytestmark = pytest.mark.integration


async def _empty_query_iter(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
    """mock query 返回空 async generator。"""
    return
    yield


class TestBuildMcpServers:
    """验证 _build_mcp_servers 辅助函数。"""

    def test_build_mcp_servers_with_gateway_url(self) -> None:
        """payload 含 gateway_url -> mcp_servers 包含 gateway 配置。"""
        result = _build_mcp_servers("https://gateway.example.com/mcp")

        assert result == {"gateway": {"type": "sse", "url": "https://gateway.example.com/mcp"}}

    def test_build_mcp_servers_without_gateway_url(self) -> None:
        """payload 无 gateway_url -> mcp_servers 为空。"""
        result = _build_mcp_servers("")

        assert result == {}

    def test_build_mcp_servers_format(self) -> None:
        """验证格式: {"gateway": {"type": "sse", "url": url}}。"""
        url = "https://gw.test.com/sse"
        result = _build_mcp_servers(url)

        assert "gateway" in result
        assert result["gateway"]["type"] == "sse"
        assert result["gateway"]["url"] == url


class TestInvokeWithGateway:
    """验证 invoke 函数中 gateway_url -> ClaudeAgentOptions.mcp_servers 传递。"""

    @pytest.mark.asyncio
    @patch("src.agent_entrypoint.query")
    async def test_invoke_with_gateway_url_builds_mcp_servers(self, mock_query: AsyncMock) -> None:
        """invoke payload 含 gateway_url -> ClaudeAgentOptions 中 mcp_servers 包含 gateway。"""
        from src.agent_entrypoint import invoke

        mock_query.return_value = _empty_query_iter()

        await invoke(
            {
                "prompt": "测试",
                "system_prompt": "",
                "gateway_url": "https://gw.example.com/mcp",
            },
        )

        # 验证 query 被调用且 options.mcp_servers 包含 gateway
        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options is not None
        assert "gateway" in options.mcp_servers
        assert options.mcp_servers["gateway"]["type"] == "sse"

    @pytest.mark.asyncio
    @patch("src.agent_entrypoint.query")
    async def test_invoke_without_gateway_url_no_mcp_servers(self, mock_query: AsyncMock) -> None:
        """invoke payload 无 gateway_url -> mcp_servers 为空。"""
        from src.agent_entrypoint import invoke

        mock_query.return_value = _empty_query_iter()

        await invoke({"prompt": "测试", "system_prompt": ""})

        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options is not None
        assert options.mcp_servers == {}
