"""集成测试: ToolCatalogService → GatewaySyncAdapter 完整链路 (mock boto3)。

验证工具审批/废弃时 Gateway 注册/注销的完整流程，
以及各种边界条件（非 MCP 类型跳过、失败不阻断等）。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.tool_catalog.application.services.tool_service import ToolCatalogService
from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.repositories.tool_repository import IToolRepository
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.shared.domain.exceptions import DomainError


# mock_event_bus 作为 fixture 注入是为了 patch event_bus 副作用, 不直接使用
# ruff: noqa: ARG002

pytestmark = pytest.mark.integration


# ── Fixture ──


def _make_mcp_tool(
    *,
    tool_id: int = 1,
    status: ToolStatus = ToolStatus.PENDING_REVIEW,
    gateway_target_id: str = "",
) -> Tool:
    """创建 MCP_SERVER 类型测试工具。"""
    return Tool(
        id=tool_id,
        name="mcp-test-tool",
        description="测试 MCP 工具",
        tool_type=ToolType.MCP_SERVER,
        version="1.0.0",
        status=status,
        creator_id=100,
        config=ToolConfig(server_url="http://mcp.example.com"),
        gateway_target_id=gateway_target_id,
    )


def _make_api_tool(*, tool_id: int = 2) -> Tool:
    """创建 API 类型测试工具。"""
    return Tool(
        id=tool_id,
        name="api-test-tool",
        description="测试 API 工具",
        tool_type=ToolType.API,
        version="1.0.0",
        status=ToolStatus.PENDING_REVIEW,
        creator_id=100,
        config=ToolConfig(endpoint_url="http://api.example.com", method="POST"),
    )


def _make_function_tool(*, tool_id: int = 3) -> Tool:
    """创建 Function 类型测试工具。"""
    return Tool(
        id=tool_id,
        name="func-test-tool",
        description="测试 Function 工具",
        tool_type=ToolType.FUNCTION,
        version="1.0.0",
        status=ToolStatus.PENDING_REVIEW,
        creator_id=100,
        config=ToolConfig(runtime="python3.11", handler="index.handler"),
    )


@pytest.fixture
def mock_tool_repo() -> AsyncMock:
    return AsyncMock(spec=IToolRepository)


@pytest.fixture
def mock_gateway_sync() -> AsyncMock:
    """Mock IGatewaySyncService。"""
    mock = AsyncMock()
    mock.register_tool = AsyncMock(return_value="target-abc-123")
    mock.unregister_tool = AsyncMock()
    return mock


@pytest.fixture
def service_with_gateway(mock_tool_repo: AsyncMock, mock_gateway_sync: AsyncMock) -> ToolCatalogService:
    """注入 mock gateway_sync 的 ToolCatalogService。"""
    return ToolCatalogService(repository=mock_tool_repo, gateway_sync=mock_gateway_sync)


@pytest.fixture
def mock_event_bus() -> MagicMock:  # type: ignore[misc]
    """Mock event_bus 避免事件副作用。"""
    with patch("src.modules.tool_catalog.application.services.tool_service.event_bus") as mock_bus:
        mock_bus.publish_async = AsyncMock()
        yield mock_bus


# ── 测试: 审批 → Gateway 注册 ──


class TestApproveToolGatewaySync:
    """审批工具时 Gateway 注册行为。"""

    @pytest.mark.asyncio
    async def test_approve_mcp_tool_registers_to_gateway(
        self,
        service_with_gateway: ToolCatalogService,
        mock_tool_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
        mock_event_bus: MagicMock,
    ) -> None:
        """审批 MCP_SERVER 工具 → gateway_sync.register_tool 被调用，gateway_target_id 非空。"""
        tool = _make_mcp_tool()
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        result = await service_with_gateway.approve_tool(tool_id=1, reviewer_id=200)

        mock_gateway_sync.register_tool.assert_called_once()
        assert result.gateway_target_id == "target-abc-123"

    @pytest.mark.asyncio
    async def test_approve_mcp_tool_target_config_format(
        self,
        service_with_gateway: ToolCatalogService,
        mock_tool_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
        mock_event_bus: MagicMock,
    ) -> None:
        """验证 register_tool 调用参数格式正确。"""
        tool = _make_mcp_tool()
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        await service_with_gateway.approve_tool(tool_id=1, reviewer_id=200)

        call_kwargs = mock_gateway_sync.register_tool.call_args.kwargs
        assert call_kwargs["tool_id"] == 1
        assert call_kwargs["tool_name"] == "mcp-test-tool"
        assert call_kwargs["server_url"] == "http://mcp.example.com"

    @pytest.mark.asyncio
    async def test_approve_api_tool_skips_gateway(
        self,
        service_with_gateway: ToolCatalogService,
        mock_tool_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
        mock_event_bus: MagicMock,
    ) -> None:
        """审批 API 类型工具 → 不调用 Gateway。"""
        tool = _make_api_tool()
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        await service_with_gateway.approve_tool(tool_id=2, reviewer_id=200)

        mock_gateway_sync.register_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_approve_function_tool_skips_gateway(
        self,
        service_with_gateway: ToolCatalogService,
        mock_tool_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
        mock_event_bus: MagicMock,
    ) -> None:
        """审批 Function 类型工具 → 不调用 Gateway。"""
        tool = _make_function_tool()
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        await service_with_gateway.approve_tool(tool_id=3, reviewer_id=200)

        mock_gateway_sync.register_tool.assert_not_called()


# ── 测试: 废弃 → Gateway 注销 ──


class TestDeprecateToolGatewaySync:
    """废弃工具时 Gateway 注销行为。"""

    @pytest.mark.asyncio
    async def test_deprecate_tool_unregisters_from_gateway(
        self,
        service_with_gateway: ToolCatalogService,
        mock_tool_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
        mock_event_bus: MagicMock,
    ) -> None:
        """废弃带有 target_id 的 MCP 工具 → gateway_sync.unregister_tool 被调用。"""
        tool = _make_mcp_tool(status=ToolStatus.APPROVED, gateway_target_id="target-abc-123")
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        result = await service_with_gateway.deprecate_tool(tool_id=1, operator_id=100)

        mock_gateway_sync.unregister_tool.assert_called_once()
        assert result.gateway_target_id == ""

    @pytest.mark.asyncio
    async def test_deprecate_tool_without_target_skips(
        self,
        service_with_gateway: ToolCatalogService,
        mock_tool_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
        mock_event_bus: MagicMock,
    ) -> None:
        """废弃无 target_id 的工具 → 跳过 Gateway 注销。"""
        tool = _make_mcp_tool(status=ToolStatus.APPROVED, gateway_target_id="")
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        await service_with_gateway.deprecate_tool(tool_id=1, operator_id=100)

        mock_gateway_sync.unregister_tool.assert_not_called()


# ── 测试: 失败容错 ──


class TestGatewayFailureResilience:
    """Gateway 同步失败不阻断业务操作。"""

    @pytest.mark.asyncio
    async def test_gateway_register_failure_not_blocking(
        self,
        service_with_gateway: ToolCatalogService,
        mock_tool_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
        mock_event_bus: MagicMock,
    ) -> None:
        """Gateway 注册失败 → 审批仍成功，gateway_target_id 为空。"""
        tool = _make_mcp_tool()
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t
        mock_gateway_sync.register_tool.side_effect = DomainError(
            message="Gateway API 失败",
            code="GATEWAY_REGISTER_ERROR",
        )

        # 审批不应抛出异常
        result = await service_with_gateway.approve_tool(tool_id=1, reviewer_id=200)

        assert result.status == "approved"
        assert result.gateway_target_id == ""

    @pytest.mark.asyncio
    async def test_gateway_unregister_failure_not_blocking(
        self,
        service_with_gateway: ToolCatalogService,
        mock_tool_repo: AsyncMock,
        mock_gateway_sync: AsyncMock,
        mock_event_bus: MagicMock,
    ) -> None:
        """Gateway 注销失败 → 废弃仍成功。"""
        tool = _make_mcp_tool(status=ToolStatus.APPROVED, gateway_target_id="target-abc-123")
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t
        mock_gateway_sync.unregister_tool.side_effect = DomainError(
            message="Gateway API 失败",
            code="GATEWAY_UNREGISTER_ERROR",
        )

        # 废弃不应抛出异常
        result = await service_with_gateway.deprecate_tool(tool_id=1, operator_id=100)

        assert result.status == "deprecated"


# ── 测试: 无 gateway_sync 配置 ──


class TestNoGatewaySync:
    """gateway_sync=None 时的行为。"""

    @pytest.mark.asyncio
    async def test_no_gateway_sync_when_none(
        self,
        mock_tool_repo: AsyncMock,
        mock_event_bus: MagicMock,
    ) -> None:
        """gateway_sync=None → 审批正常完成，无 Gateway 调用。"""
        service = ToolCatalogService(repository=mock_tool_repo, gateway_sync=None)
        tool = _make_mcp_tool()
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        result = await service.approve_tool(tool_id=1, reviewer_id=200)

        assert result.status == "approved"
        assert result.gateway_target_id == ""
