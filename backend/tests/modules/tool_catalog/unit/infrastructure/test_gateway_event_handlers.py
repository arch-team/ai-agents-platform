"""Gateway 事件处理器单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.tool_catalog.domain.events import ToolApprovedEvent, ToolDeprecatedEvent
from src.modules.tool_catalog.infrastructure.external.gateway_event_handlers import (
    handle_tool_approved,
    handle_tool_deprecated,
)


class TestHandleToolApproved:
    """ToolApprovedEvent 处理器测试。"""

    @pytest.mark.asyncio
    async def test_registers_mcp_server_tool_to_gateway(self):
        mock_repo = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.id = 1
        mock_tool.name = "my-mcp-server"
        mock_tool.description = "MCP 工具"
        mock_tool.tool_type.value = "mcp_server"
        mock_tool.config.server_url = "https://example.com/mcp"
        mock_tool.config.transport = "sse"
        mock_tool.gateway_target_id = ""
        mock_repo.get_by_id.return_value = mock_tool

        mock_sync = AsyncMock()
        mock_sync.register_tool.return_value = "target-new-123"

        event = ToolApprovedEvent(tool_id=1, creator_id=10, reviewer_id=20)

        await handle_tool_approved(event, repo=mock_repo, gateway_sync=mock_sync)

        mock_sync.register_tool.assert_called_once_with(
            tool_id=1,
            tool_name="my-mcp-server",
            description="MCP 工具",
            server_url="https://example.com/mcp",
            transport="sse",
        )
        # 应该更新 tool 的 gateway_target_id
        assert mock_tool.gateway_target_id == "target-new-123"
        mock_repo.update.assert_called_once_with(mock_tool)

    @pytest.mark.asyncio
    async def test_skips_non_mcp_server_tools(self):
        mock_repo = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.id = 2
        mock_tool.tool_type.value = "api"
        mock_repo.get_by_id.return_value = mock_tool

        mock_sync = AsyncMock()

        event = ToolApprovedEvent(tool_id=2, creator_id=10, reviewer_id=20)

        await handle_tool_approved(event, repo=mock_repo, gateway_sync=mock_sync)

        mock_sync.register_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_tool_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        mock_sync = AsyncMock()

        event = ToolApprovedEvent(tool_id=999, creator_id=10, reviewer_id=20)

        await handle_tool_approved(event, repo=mock_repo, gateway_sync=mock_sync)

        mock_sync.register_tool.assert_not_called()


class TestHandleToolDeprecated:
    """ToolDeprecatedEvent 处理器测试。"""

    @pytest.mark.asyncio
    async def test_unregisters_tool_from_gateway(self):
        mock_repo = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.id = 1
        mock_tool.tool_type.value = "mcp_server"
        mock_tool.gateway_target_id = "target-old-456"
        mock_repo.get_by_id.return_value = mock_tool

        mock_sync = AsyncMock()

        event = ToolDeprecatedEvent(tool_id=1, creator_id=10)

        await handle_tool_deprecated(event, repo=mock_repo, gateway_sync=mock_sync)

        mock_sync.unregister_tool.assert_called_once_with(
            tool_id=1,
            target_id="target-old-456",
        )
        assert mock_tool.gateway_target_id == ""
        mock_repo.update.assert_called_once_with(mock_tool)

    @pytest.mark.asyncio
    async def test_skips_when_no_gateway_target_id(self):
        mock_repo = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.id = 1
        mock_tool.tool_type.value = "mcp_server"
        mock_tool.gateway_target_id = ""
        mock_repo.get_by_id.return_value = mock_tool

        mock_sync = AsyncMock()

        event = ToolDeprecatedEvent(tool_id=1, creator_id=10)

        await handle_tool_deprecated(event, repo=mock_repo, gateway_sync=mock_sync)

        mock_sync.unregister_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_tool_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        mock_sync = AsyncMock()

        event = ToolDeprecatedEvent(tool_id=999, creator_id=10)

        await handle_tool_deprecated(event, repo=mock_repo, gateway_sync=mock_sync)

        mock_sync.unregister_tool.assert_not_called()
