"""集成测试: 事件处理器 → Gateway 同步触发链路。

验证 handle_tool_approved / handle_tool_deprecated 事件处理器
通过 IGatewaySyncService 正确触发 Gateway 注册/注销。
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.events import ToolApprovedEvent, ToolDeprecatedEvent
from src.modules.tool_catalog.domain.repositories.tool_repository import IToolRepository
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.modules.tool_catalog.infrastructure.external.gateway_event_handlers import (
    handle_tool_approved,
    handle_tool_deprecated,
)
from src.shared.domain.exceptions import DomainError


pytestmark = pytest.mark.integration


# ── Fixture ──


def _make_mcp_tool(
    *,
    tool_id: int = 1,
    status: ToolStatus = ToolStatus.APPROVED,
    gateway_target_id: str = "",
) -> Tool:
    return Tool(
        id=tool_id,
        name="event-mcp-tool",
        description="事件测试工具",
        tool_type=ToolType.MCP_SERVER,
        version="1.0.0",
        status=status,
        creator_id=100,
        config=ToolConfig(server_url="http://mcp.example.com"),
        gateway_target_id=gateway_target_id,
    )


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=IToolRepository)


@pytest.fixture
def mock_gateway_sync() -> AsyncMock:
    mock = AsyncMock()
    mock.register_tool = AsyncMock(return_value="target-event-123")
    mock.unregister_tool = AsyncMock()
    return mock


# ── 测试 ──


class TestGatewayEventHandlers:
    """事件处理器 Gateway 同步验证。"""

    @pytest.mark.asyncio
    async def test_approved_event_triggers_register(
        self,
        mock_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
    ) -> None:
        """ToolApprovedEvent → register_tool 被调用，target_id 回写到 tool。"""
        tool = _make_mcp_tool()
        mock_repo.get_by_id.return_value = tool
        mock_repo.update.side_effect = lambda t: t

        event = ToolApprovedEvent(tool_id=1, creator_id=100, reviewer_id=200)
        await handle_tool_approved(event, repo=mock_repo, gateway_sync=mock_gateway_sync)

        mock_gateway_sync.register_tool.assert_called_once()
        # target_id 应回写到 tool 实体
        assert tool.gateway_target_id == "target-event-123"
        mock_repo.update.assert_called_once_with(tool)

    @pytest.mark.asyncio
    async def test_deprecated_event_triggers_unregister(
        self,
        mock_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
    ) -> None:
        """ToolDeprecatedEvent → unregister_tool 被调用，target_id 清空。"""
        tool = _make_mcp_tool(gateway_target_id="target-event-123")
        mock_repo.get_by_id.return_value = tool

        event = ToolDeprecatedEvent(tool_id=1, creator_id=100)
        await handle_tool_deprecated(event, repo=mock_repo, gateway_sync=mock_gateway_sync)

        mock_gateway_sync.unregister_tool.assert_called_once_with(
            tool_id=1,
            target_id="target-event-123",
        )
        assert tool.gateway_target_id == ""
        mock_repo.update.assert_called_once_with(tool)

    @pytest.mark.asyncio
    async def test_event_handler_resilient_to_failure(
        self,
        mock_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
    ) -> None:
        """Gateway 异常不导致事件处理器 crash。"""
        tool = _make_mcp_tool()
        mock_repo.get_by_id.return_value = tool
        mock_gateway_sync.register_tool.side_effect = DomainError(message="Gateway 不可达", code="GATEWAY_ERROR")

        event = ToolApprovedEvent(tool_id=1, creator_id=100, reviewer_id=200)
        # 不应抛出异常
        await handle_tool_approved(event, repo=mock_repo, gateway_sync=mock_gateway_sync)

        # target_id 不应变更
        assert tool.gateway_target_id == ""

    @pytest.mark.asyncio
    async def test_full_approve_deprecate_cycle(
        self,
        mock_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
    ) -> None:
        """完整审批 → 废弃循环: target_id 先填充后清空。"""
        tool = _make_mcp_tool()
        mock_repo.get_by_id.return_value = tool
        mock_repo.update.side_effect = lambda t: t

        # 1. 审批 → 注册
        approve_event = ToolApprovedEvent(tool_id=1, creator_id=100, reviewer_id=200)
        await handle_tool_approved(approve_event, repo=mock_repo, gateway_sync=mock_gateway_sync)
        assert tool.gateway_target_id == "target-event-123"

        # 2. 废弃 → 注销
        deprecate_event = ToolDeprecatedEvent(tool_id=1, creator_id=100)
        await handle_tool_deprecated(deprecate_event, repo=mock_repo, gateway_sync=mock_gateway_sync)
        assert tool.gateway_target_id == ""
