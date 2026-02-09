"""ToolCatalogService 测试。"""

import pytest
from unittest.mock import AsyncMock, patch

from src.modules.tool_catalog.application.dto.tool_dto import (
    CreateToolDTO,
    UpdateToolDTO,
)
from src.modules.tool_catalog.application.services.tool_service import (
    ToolCatalogService,
)
from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.exceptions import (
    ToolNameDuplicateError,
    ToolNotFoundError,
)
from src.modules.tool_catalog.domain.repositories.tool_repository import (
    IToolRepository,
)
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.shared.domain.exceptions import (
    DomainError,
    InvalidStateTransitionError,
)


EVENT_BUS_PATH = "src.modules.tool_catalog.application.services.tool_service.event_bus"


def _make_tool(
    *,
    tool_id: int = 1,
    name: str = "测试 Tool",
    description: str = "描述",
    tool_type: ToolType = ToolType.MCP_SERVER,
    version: str = "1.0.0",
    status: ToolStatus = ToolStatus.DRAFT,
    creator_id: int = 100,
    config: ToolConfig | None = None,
    reviewer_id: int | None = None,
    review_comment: str = "",
    allowed_roles: tuple[str, ...] = ("admin", "developer"),
) -> Tool:
    return Tool(
        id=tool_id,
        name=name,
        description=description,
        tool_type=tool_type,
        version=version,
        status=status,
        creator_id=creator_id,
        config=config or ToolConfig(server_url="http://localhost:3000"),
        reviewer_id=reviewer_id,
        review_comment=review_comment,
        allowed_roles=allowed_roles,
    )


def _make_service(mock_repo: AsyncMock) -> ToolCatalogService:
    return ToolCatalogService(mock_repo)


@pytest.mark.unit
class TestToolCatalogServiceCreate:
    @pytest.mark.asyncio
    async def test_create_tool_success(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_name_and_creator.return_value = None
        mock_repo.create.side_effect = lambda t: _make_tool(
            name=t.name, description=t.description, creator_id=t.creator_id,
            tool_type=t.tool_type,
        )

        service = _make_service(mock_repo)
        dto = CreateToolDTO(name="新 Tool", tool_type="mcp_server", description="新描述")

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.create_tool(dto, creator_id=100)

        assert result.name == "新 Tool"
        assert result.description == "新描述"
        assert result.tool_type == "mcp_server"
        assert result.status == "draft"
        assert result.creator_id == 100
        mock_repo.create.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tool_duplicate_name_raises(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_name_and_creator.return_value = _make_tool(name="已存在")

        service = _make_service(mock_repo)
        dto = CreateToolDTO(name="已存在", tool_type="mcp_server")

        with pytest.raises(ToolNameDuplicateError):
            await service.create_tool(dto, creator_id=100)

        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_tool_uses_dto_config(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_name_and_creator.return_value = None
        created_tool: Tool | None = None

        async def capture_create(tool: Tool) -> Tool:
            nonlocal created_tool
            created_tool = tool
            return _make_tool(
                name=tool.name,
                creator_id=tool.creator_id,
                tool_type=tool.tool_type,
                config=tool.config,
                allowed_roles=tool.allowed_roles,
            )

        mock_repo.create.side_effect = capture_create

        service = _make_service(mock_repo)
        dto = CreateToolDTO(
            name="自定义配置",
            tool_type="api",
            endpoint_url="https://api.example.com",
            method="GET",
            headers=[("Authorization", "Bearer xxx")],
            auth_type="api_key",
            auth_config=[("key", "my-key")],
            allowed_roles=["admin"],
        )

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.create_tool(dto, creator_id=100)

        assert created_tool is not None
        assert created_tool.config.endpoint_url == "https://api.example.com"
        assert created_tool.config.method == "GET"
        assert created_tool.config.headers == (("Authorization", "Bearer xxx"),)
        assert created_tool.config.auth_type == "api_key"
        assert created_tool.config.auth_config == (("key", "my-key"),)
        assert created_tool.allowed_roles == ("admin",)
        assert result.allowed_roles == ["admin"]


@pytest.mark.unit
class TestToolCatalogServiceGet:
    @pytest.mark.asyncio
    async def test_get_tool_returns_dto(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = _make_tool()

        service = _make_service(mock_repo)
        result = await service.get_tool(1)

        assert result.id == 1
        assert result.name == "测试 Tool"

    @pytest.mark.asyncio
    async def test_get_tool_not_found_raises(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = None

        service = _make_service(mock_repo)

        with pytest.raises(ToolNotFoundError):
            await service.get_tool(9999)

    @pytest.mark.asyncio
    async def test_get_owned_tool_success(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = _make_tool(creator_id=100)

        service = _make_service(mock_repo)
        result = await service.get_owned_tool(1, operator_id=100)

        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_owned_tool_non_owner_raises(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = _make_tool(creator_id=100)

        service = _make_service(mock_repo)

        with pytest.raises(DomainError, match="无权操作"):
            await service.get_owned_tool(1, operator_id=999)


@pytest.mark.unit
class TestToolCatalogServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_draft_tool_success(self) -> None:
        tool = _make_tool(status=ToolStatus.DRAFT)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool
        mock_repo.get_by_name_and_creator.return_value = None
        mock_repo.update.side_effect = lambda t: t

        service = _make_service(mock_repo)
        dto = UpdateToolDTO(name="新名称", description="新描述")

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.update_tool(1, dto, operator_id=100)

        assert result.name == "新名称"
        assert result.description == "新描述"
        mock_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_rejected_tool_success(self) -> None:
        tool = _make_tool(status=ToolStatus.REJECTED)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool
        mock_repo.get_by_name_and_creator.return_value = None
        mock_repo.update.side_effect = lambda t: t

        service = _make_service(mock_repo)
        dto = UpdateToolDTO(name="修改名称")

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.update_tool(1, dto, operator_id=100)

        assert result.name == "修改名称"

    @pytest.mark.asyncio
    async def test_update_non_owner_raises(self) -> None:
        tool = _make_tool(creator_id=100)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)
        dto = UpdateToolDTO(name="新名称")

        with pytest.raises(DomainError, match="无权操作"):
            await service.update_tool(1, dto, operator_id=999)

    @pytest.mark.asyncio
    async def test_update_approved_tool_raises(self) -> None:
        tool = _make_tool(status=ToolStatus.APPROVED)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)
        dto = UpdateToolDTO(name="新名称")

        with pytest.raises(InvalidStateTransitionError):
            await service.update_tool(1, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_duplicate_name_raises(self) -> None:
        tool = _make_tool(status=ToolStatus.DRAFT, name="原始名称")
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool
        mock_repo.get_by_name_and_creator.return_value = _make_tool(
            tool_id=2, name="已存在"
        )

        service = _make_service(mock_repo)
        dto = UpdateToolDTO(name="已存在")

        with pytest.raises(ToolNameDuplicateError):
            await service.update_tool(1, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_partial_fields(self) -> None:
        tool = _make_tool(status=ToolStatus.DRAFT)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool
        mock_repo.update.side_effect = lambda t: t

        service = _make_service(mock_repo)
        dto = UpdateToolDTO(server_url="http://new-server:3000")

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.update_tool(1, dto, operator_id=100)

        assert result.server_url == "http://new-server:3000"
        # 其他字段不变
        assert result.name == "测试 Tool"


@pytest.mark.unit
class TestToolCatalogServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_draft_tool_success(self) -> None:
        tool = _make_tool(status=ToolStatus.DRAFT)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            await service.delete_tool(1, operator_id=100)

        mock_repo.delete.assert_called_once_with(1)
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_non_draft_raises(self) -> None:
        tool = _make_tool(status=ToolStatus.APPROVED)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)

        with pytest.raises(InvalidStateTransitionError):
            await service.delete_tool(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_delete_non_owner_raises(self) -> None:
        tool = _make_tool(creator_id=100)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)

        with pytest.raises(DomainError, match="无权操作"):
            await service.delete_tool(1, operator_id=999)


@pytest.mark.unit
class TestToolCatalogServiceList:
    @pytest.mark.asyncio
    async def test_list_tools_returns_paged_result(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.list_filtered.return_value = [
            _make_tool(tool_id=1, name="T1"),
            _make_tool(tool_id=2, name="T2"),
        ]
        mock_repo.count_filtered.return_value = 2

        service = _make_service(mock_repo)
        result = await service.list_tools(creator_id=100)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_tools_empty(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.list_filtered.return_value = []
        mock_repo.count_filtered.return_value = 0

        service = _make_service(mock_repo)
        result = await service.list_tools(creator_id=100)

        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_tools_with_filters(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.list_filtered.return_value = [
            _make_tool(tool_id=1, status=ToolStatus.APPROVED),
        ]
        mock_repo.count_filtered.return_value = 1

        service = _make_service(mock_repo)
        result = await service.list_tools(
            creator_id=100,
            status=ToolStatus.APPROVED,
            tool_type=ToolType.MCP_SERVER,
            keyword="测试",
        )

        assert result.total == 1
        mock_repo.list_filtered.assert_called_once_with(
            creator_id=100,
            status=ToolStatus.APPROVED,
            tool_type=ToolType.MCP_SERVER,
            keyword="测试",
            offset=0,
            limit=20,
        )

    @pytest.mark.asyncio
    async def test_list_tools_pagination(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.list_filtered.return_value = [
            _make_tool(tool_id=3, name="T3"),
        ]
        mock_repo.count_filtered.return_value = 5

        service = _make_service(mock_repo)
        result = await service.list_tools(creator_id=100, page=2, page_size=2)

        assert result.page == 2
        assert result.page_size == 2
        assert result.total == 5
        mock_repo.list_filtered.assert_called_once_with(
            creator_id=100,
            status=None,
            tool_type=None,
            keyword=None,
            offset=2,
            limit=2,
        )


@pytest.mark.unit
class TestToolCatalogServiceListApproved:
    @pytest.mark.asyncio
    async def test_list_approved_tools_returns_paged_result(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.list_approved.return_value = [
            _make_tool(tool_id=1, status=ToolStatus.APPROVED),
        ]
        mock_repo.count_approved.return_value = 1

        service = _make_service(mock_repo)
        result = await service.list_approved_tools()

        assert result.total == 1
        assert len(result.items) == 1
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_list_approved_tools_empty(self) -> None:
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.list_approved.return_value = []
        mock_repo.count_approved.return_value = 0

        service = _make_service(mock_repo)
        result = await service.list_approved_tools()

        assert result.total == 0
        assert result.items == []


@pytest.mark.unit
class TestToolCatalogServiceSubmit:
    @pytest.mark.asyncio
    async def test_submit_draft_tool_success(self) -> None:
        tool = _make_tool(
            status=ToolStatus.DRAFT,
            description="有描述",
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool
        mock_repo.update.side_effect = lambda t: t

        service = _make_service(mock_repo)

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.submit_for_review(1, operator_id=100)

        assert result.status == "pending_review"
        mock_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_non_draft_raises(self) -> None:
        tool = _make_tool(status=ToolStatus.APPROVED)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)

        with pytest.raises(InvalidStateTransitionError):
            await service.submit_for_review(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_submit_non_owner_raises(self) -> None:
        tool = _make_tool(creator_id=100)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)

        with pytest.raises(DomainError, match="无权操作"):
            await service.submit_for_review(1, operator_id=999)


@pytest.mark.unit
class TestToolCatalogServiceApprove:
    @pytest.mark.asyncio
    async def test_approve_pending_tool_success(self) -> None:
        tool = _make_tool(
            status=ToolStatus.PENDING_REVIEW,
            description="有描述",
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool
        mock_repo.update.side_effect = lambda t: t

        service = _make_service(mock_repo)

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.approve_tool(1, reviewer_id=200)

        assert result.status == "approved"
        assert result.reviewer_id == 200
        mock_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_non_pending_raises(self) -> None:
        tool = _make_tool(status=ToolStatus.DRAFT)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)

        with pytest.raises(InvalidStateTransitionError):
            await service.approve_tool(1, reviewer_id=200)


@pytest.mark.unit
class TestToolCatalogServiceReject:
    @pytest.mark.asyncio
    async def test_reject_pending_tool_success(self) -> None:
        tool = _make_tool(
            status=ToolStatus.PENDING_REVIEW,
            description="有描述",
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool
        mock_repo.update.side_effect = lambda t: t

        service = _make_service(mock_repo)

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.reject_tool(1, reviewer_id=200, comment="需要改进")

        assert result.status == "rejected"
        assert result.reviewer_id == 200
        assert result.review_comment == "需要改进"
        mock_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_non_pending_raises(self) -> None:
        tool = _make_tool(status=ToolStatus.DRAFT)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)

        with pytest.raises(InvalidStateTransitionError):
            await service.reject_tool(1, reviewer_id=200, comment="不行")

    @pytest.mark.asyncio
    async def test_reject_records_comment(self) -> None:
        tool = _make_tool(
            status=ToolStatus.PENDING_REVIEW,
            description="有描述",
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool
        mock_repo.update.side_effect = lambda t: t

        service = _make_service(mock_repo)

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.reject_tool(
                1, reviewer_id=200, comment="描述不够详细"
            )

        assert result.review_comment == "描述不够详细"
        # 验证事件携带 comment
        event = mock_bus.publish_async.call_args[0][0]
        assert event.comment == "描述不够详细"


@pytest.mark.unit
class TestToolCatalogServiceDeprecate:
    @pytest.mark.asyncio
    async def test_deprecate_approved_tool_success(self) -> None:
        tool = _make_tool(status=ToolStatus.APPROVED)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool
        mock_repo.update.side_effect = lambda t: t

        service = _make_service(mock_repo)

        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.deprecate_tool(1, operator_id=100)

        assert result.status == "deprecated"
        mock_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_deprecate_non_approved_raises(self) -> None:
        tool = _make_tool(status=ToolStatus.DRAFT)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)

        with pytest.raises(InvalidStateTransitionError):
            await service.deprecate_tool(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_deprecate_non_owner_raises(self) -> None:
        tool = _make_tool(status=ToolStatus.APPROVED, creator_id=100)
        mock_repo = AsyncMock(spec=IToolRepository)
        mock_repo.get_by_id.return_value = tool

        service = _make_service(mock_repo)

        with pytest.raises(DomainError, match="无权操作"):
            await service.deprecate_tool(1, operator_id=999)
