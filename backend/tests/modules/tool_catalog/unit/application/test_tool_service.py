"""ToolCatalogService 测试。"""

import pytest
from unittest.mock import AsyncMock

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
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.shared.domain.exceptions import (
    DomainError,
    InvalidStateTransitionError,
)

from tests.modules.tool_catalog.conftest import make_tool


@pytest.mark.unit
class TestToolCatalogServiceCreate:
    @pytest.mark.asyncio
    async def test_create_tool_success(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        mock_tool_repo.get_by_name_and_creator.return_value = None
        mock_tool_repo.create.side_effect = lambda t: make_tool(
            name=t.name, description=t.description, creator_id=t.creator_id,
            tool_type=t.tool_type,
        )

        dto = CreateToolDTO(name="新 Tool", tool_type="mcp_server", description="新描述")
        result = await tool_service.create_tool(dto, creator_id=100)

        assert result.name == "新 Tool"
        assert result.description == "新描述"
        assert result.tool_type == "mcp_server"
        assert result.status == "draft"
        assert result.creator_id == 100
        mock_tool_repo.create.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tool_duplicate_name_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_name_and_creator.return_value = make_tool(name="已存在")

        dto = CreateToolDTO(name="已存在", tool_type="mcp_server")

        with pytest.raises(ToolNameDuplicateError):
            await tool_service.create_tool(dto, creator_id=100)

        mock_tool_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_tool_uses_dto_config(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        mock_tool_repo.get_by_name_and_creator.return_value = None
        created_tool: Tool | None = None

        async def capture_create(tool: Tool) -> Tool:
            nonlocal created_tool
            created_tool = tool
            return make_tool(
                name=tool.name,
                creator_id=tool.creator_id,
                tool_type=tool.tool_type,
                config=tool.config,
                allowed_roles=tool.allowed_roles,
            )

        mock_tool_repo.create.side_effect = capture_create

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
        result = await tool_service.create_tool(dto, creator_id=100)

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
    async def test_get_tool_returns_dto(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool()

        result = await tool_service.get_tool(1)

        assert result.id == 1
        assert result.name == "测试 Tool"

    @pytest.mark.asyncio
    async def test_get_tool_not_found_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = None

        with pytest.raises(ToolNotFoundError):
            await tool_service.get_tool(9999)

    @pytest.mark.asyncio
    async def test_get_owned_tool_success(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(creator_id=100)

        result = await tool_service.get_owned_tool(1, operator_id=100)

        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_owned_tool_non_owner_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(creator_id=100)

        with pytest.raises(DomainError, match="无权操作"):
            await tool_service.get_owned_tool(1, operator_id=999)


@pytest.mark.unit
class TestToolCatalogServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_draft_tool_success(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.DRAFT)
        mock_tool_repo.get_by_name_and_creator.return_value = None
        mock_tool_repo.update.side_effect = lambda t: t

        dto = UpdateToolDTO(name="新名称", description="新描述")
        result = await tool_service.update_tool(1, dto, operator_id=100)

        assert result.name == "新名称"
        assert result.description == "新描述"
        mock_tool_repo.update.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_rejected_tool_success(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.REJECTED)
        mock_tool_repo.get_by_name_and_creator.return_value = None
        mock_tool_repo.update.side_effect = lambda t: t

        dto = UpdateToolDTO(name="修改名称")
        result = await tool_service.update_tool(1, dto, operator_id=100)

        assert result.name == "修改名称"

    @pytest.mark.asyncio
    async def test_update_non_owner_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(creator_id=100)

        dto = UpdateToolDTO(name="新名称")

        with pytest.raises(DomainError, match="无权操作"):
            await tool_service.update_tool(1, dto, operator_id=999)

    @pytest.mark.asyncio
    async def test_update_approved_tool_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.APPROVED)

        dto = UpdateToolDTO(name="新名称")

        with pytest.raises(InvalidStateTransitionError):
            await tool_service.update_tool(1, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_duplicate_name_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.DRAFT, name="原始名称")
        mock_tool_repo.get_by_name_and_creator.return_value = make_tool(
            tool_id=2, name="已存在"
        )

        dto = UpdateToolDTO(name="已存在")

        with pytest.raises(ToolNameDuplicateError):
            await tool_service.update_tool(1, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_partial_fields(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.DRAFT)
        mock_tool_repo.update.side_effect = lambda t: t

        dto = UpdateToolDTO(server_url="http://new-server:3000")
        result = await tool_service.update_tool(1, dto, operator_id=100)

        assert result.server_url == "http://new-server:3000"
        assert result.name == "测试 Tool"


@pytest.mark.unit
class TestToolCatalogServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_draft_tool_success(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.DRAFT)

        await tool_service.delete_tool(1, operator_id=100)

        mock_tool_repo.delete.assert_called_once_with(1)
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_non_draft_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.APPROVED)

        with pytest.raises(InvalidStateTransitionError):
            await tool_service.delete_tool(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_delete_non_owner_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(creator_id=100)

        with pytest.raises(DomainError, match="无权操作"):
            await tool_service.delete_tool(1, operator_id=999)


@pytest.mark.unit
class TestToolCatalogServiceList:
    @pytest.mark.asyncio
    async def test_list_tools_returns_paged_result(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.list_filtered.return_value = [
            make_tool(tool_id=1, name="T1"),
            make_tool(tool_id=2, name="T2"),
        ]
        mock_tool_repo.count_filtered.return_value = 2

        result = await tool_service.list_tools(creator_id=100)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_tools_empty(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.list_filtered.return_value = []
        mock_tool_repo.count_filtered.return_value = 0

        result = await tool_service.list_tools(creator_id=100)

        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_tools_with_filters(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.list_filtered.return_value = [
            make_tool(tool_id=1, status=ToolStatus.APPROVED),
        ]
        mock_tool_repo.count_filtered.return_value = 1

        result = await tool_service.list_tools(
            creator_id=100,
            status=ToolStatus.APPROVED,
            tool_type=ToolType.MCP_SERVER,
            keyword="测试",
        )

        assert result.total == 1
        mock_tool_repo.list_filtered.assert_called_once_with(
            creator_id=100,
            status=ToolStatus.APPROVED,
            tool_type=ToolType.MCP_SERVER,
            keyword="测试",
            offset=0,
            limit=20,
        )

    @pytest.mark.asyncio
    async def test_list_tools_pagination(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.list_filtered.return_value = [
            make_tool(tool_id=3, name="T3"),
        ]
        mock_tool_repo.count_filtered.return_value = 5

        result = await tool_service.list_tools(creator_id=100, page=2, page_size=2)

        assert result.page == 2
        assert result.page_size == 2
        assert result.total == 5
        mock_tool_repo.list_filtered.assert_called_once_with(
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
    async def test_list_approved_tools_returns_paged_result(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.list_approved.return_value = [
            make_tool(tool_id=1, status=ToolStatus.APPROVED),
        ]
        mock_tool_repo.count_approved.return_value = 1

        result = await tool_service.list_approved_tools()

        assert result.total == 1
        assert len(result.items) == 1
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_list_approved_tools_empty(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.list_approved.return_value = []
        mock_tool_repo.count_approved.return_value = 0

        result = await tool_service.list_approved_tools()

        assert result.total == 0
        assert result.items == []


@pytest.mark.unit
class TestToolCatalogServiceSubmit:
    @pytest.mark.asyncio
    async def test_submit_draft_tool_success(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        tool = make_tool(
            status=ToolStatus.DRAFT,
            description="有描述",
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        result = await tool_service.submit_for_review(1, operator_id=100)

        assert result.status == "pending_review"
        mock_tool_repo.update.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_non_draft_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.APPROVED)

        with pytest.raises(InvalidStateTransitionError):
            await tool_service.submit_for_review(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_submit_non_owner_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(creator_id=100)

        with pytest.raises(DomainError, match="无权操作"):
            await tool_service.submit_for_review(1, operator_id=999)


@pytest.mark.unit
class TestToolCatalogServiceApprove:
    @pytest.mark.asyncio
    async def test_approve_pending_tool_success(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        tool = make_tool(
            status=ToolStatus.PENDING_REVIEW,
            description="有描述",
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        result = await tool_service.approve_tool(1, reviewer_id=200)

        assert result.status == "approved"
        assert result.reviewer_id == 200
        mock_tool_repo.update.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_non_pending_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.DRAFT)

        with pytest.raises(InvalidStateTransitionError):
            await tool_service.approve_tool(1, reviewer_id=200)


@pytest.mark.unit
class TestToolCatalogServiceReject:
    @pytest.mark.asyncio
    async def test_reject_pending_tool_success(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        tool = make_tool(
            status=ToolStatus.PENDING_REVIEW,
            description="有描述",
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        result = await tool_service.reject_tool(1, reviewer_id=200, comment="需要改进")

        assert result.status == "rejected"
        assert result.reviewer_id == 200
        assert result.review_comment == "需要改进"
        mock_tool_repo.update.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_non_pending_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.DRAFT)

        with pytest.raises(InvalidStateTransitionError):
            await tool_service.reject_tool(1, reviewer_id=200, comment="不行")

    @pytest.mark.asyncio
    async def test_reject_records_comment(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        tool = make_tool(
            status=ToolStatus.PENDING_REVIEW,
            description="有描述",
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        mock_tool_repo.get_by_id.return_value = tool
        mock_tool_repo.update.side_effect = lambda t: t

        result = await tool_service.reject_tool(
            1, reviewer_id=200, comment="描述不够详细"
        )

        assert result.review_comment == "描述不够详细"
        event = mock_event_bus.publish_async.call_args[0][0]
        assert event.comment == "描述不够详细"


@pytest.mark.unit
class TestToolCatalogServiceDeprecate:
    @pytest.mark.asyncio
    async def test_deprecate_approved_tool_success(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService, mock_event_bus: AsyncMock
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.APPROVED)
        mock_tool_repo.update.side_effect = lambda t: t

        result = await tool_service.deprecate_tool(1, operator_id=100)

        assert result.status == "deprecated"
        mock_tool_repo.update.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_deprecate_non_approved_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.DRAFT)

        with pytest.raises(InvalidStateTransitionError):
            await tool_service.deprecate_tool(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_deprecate_non_owner_raises(
        self, mock_tool_repo: AsyncMock, tool_service: ToolCatalogService
    ) -> None:
        mock_tool_repo.get_by_id.return_value = make_tool(status=ToolStatus.APPROVED, creator_id=100)

        with pytest.raises(DomainError, match="无权操作"):
            await tool_service.deprecate_tool(1, operator_id=999)
