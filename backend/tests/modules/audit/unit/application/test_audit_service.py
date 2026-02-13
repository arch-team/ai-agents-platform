"""AuditService 单元测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.audit.application.dto.audit_log_dto import (
    CreateAuditLogDTO,
)
from src.modules.audit.application.services.audit_service import AuditService
from src.modules.audit.domain.entities.audit_log import AuditAction, AuditCategory
from src.modules.audit.domain.exceptions import AuditNotFoundError

from tests.modules.audit.conftest import make_audit_log


@pytest.mark.unit
class TestAuditServiceRecord:
    @pytest.mark.asyncio
    async def test_record_success(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_audit_repo.create.side_effect = lambda e: make_audit_log(
            actor_id=e.actor_id,
            actor_name=e.actor_name,
            action=e.action,
            category=e.category,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            module=e.module,
        )

        dto = CreateAuditLogDTO(
            actor_id=100,
            actor_name="管理员",
            action="create",
            category="agent_management",
            resource_type="agent",
            resource_id="42",
            module="agents",
        )
        result = await audit_service.record(dto)

        assert result.actor_id == 100
        assert result.actor_name == "管理员"
        assert result.action == "create"
        assert result.category == "agent_management"
        mock_audit_repo.create.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_with_failure_result(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_audit_repo.create.side_effect = lambda e: make_audit_log(
            actor_id=e.actor_id,
            actor_name=e.actor_name,
            action=e.action,
            category=e.category,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            module=e.module,
            result=e.result,
            error_message=e.error_message,
        )

        dto = CreateAuditLogDTO(
            actor_id=100,
            actor_name="管理员",
            action="delete",
            category="agent_management",
            resource_type="agent",
            resource_id="42",
            module="agents",
            result="failure",
            error_message="权限不足",
        )
        result = await audit_service.record(dto)

        assert result.result == "failure"
        assert result.error_message == "权限不足"

    @pytest.mark.asyncio
    async def test_record_with_details(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_audit_repo.create.side_effect = lambda e: make_audit_log(
            actor_id=e.actor_id,
            actor_name=e.actor_name,
            action=e.action,
            category=e.category,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            module=e.module,
            details=e.details,
        )

        dto = CreateAuditLogDTO(
            actor_id=100,
            actor_name="管理员",
            action="update",
            category="agent_management",
            resource_type="agent",
            resource_id="42",
            module="agents",
            details={"changed_field": "name", "old_value": "旧名称"},
        )
        result = await audit_service.record(dto)

        assert result.details == {"changed_field": "name", "old_value": "旧名称"}


@pytest.mark.unit
class TestAuditServiceGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
    ) -> None:
        mock_audit_repo.get_by_id.return_value = make_audit_log(audit_log_id=42)

        result = await audit_service.get_by_id(42)

        assert result.id == 42
        mock_audit_repo.get_by_id.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found_raises(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
    ) -> None:
        mock_audit_repo.get_by_id.return_value = None

        with pytest.raises(AuditNotFoundError):
            await audit_service.get_by_id(999)


@pytest.mark.unit
class TestAuditServiceListFiltered:
    @pytest.mark.asyncio
    async def test_list_filtered_success(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
    ) -> None:
        logs = [make_audit_log(audit_log_id=i) for i in range(1, 4)]
        mock_audit_repo.list_filtered.return_value = (logs, 3)

        result = await audit_service.list_filtered(page=1, page_size=20)

        assert len(result.items) == 3
        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_filtered_with_category(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
    ) -> None:
        mock_audit_repo.list_filtered.return_value = ([], 0)

        await audit_service.list_filtered(category="authentication")

        call_kwargs = mock_audit_repo.list_filtered.call_args.kwargs
        assert call_kwargs["category"] == AuditCategory.AUTHENTICATION

    @pytest.mark.asyncio
    async def test_list_filtered_with_action(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
    ) -> None:
        mock_audit_repo.list_filtered.return_value = ([], 0)

        await audit_service.list_filtered(action="login")

        call_kwargs = mock_audit_repo.list_filtered.call_args.kwargs
        assert call_kwargs["action"] == AuditAction.LOGIN

    @pytest.mark.asyncio
    async def test_list_filtered_with_date_range(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
    ) -> None:
        mock_audit_repo.list_filtered.return_value = ([], 0)
        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = datetime(2026, 1, 31, tzinfo=UTC)

        await audit_service.list_filtered(start_date=start, end_date=end)

        call_kwargs = mock_audit_repo.list_filtered.call_args.kwargs
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end


@pytest.mark.unit
class TestAuditServiceGetStats:
    @pytest.mark.asyncio
    async def test_get_stats_success(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
    ) -> None:
        mock_audit_repo.count_by_category.return_value = {
            "agent_management": 10,
            "authentication": 5,
        }
        mock_audit_repo.count_by_action.return_value = {
            "create": 8,
            "login": 5,
            "update": 2,
        }

        result = await audit_service.get_stats()

        assert result.by_category == {"agent_management": 10, "authentication": 5}
        assert result.by_action == {"create": 8, "login": 5, "update": 2}
        assert result.total == 15

    @pytest.mark.asyncio
    async def test_get_stats_empty(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
    ) -> None:
        mock_audit_repo.count_by_category.return_value = {}
        mock_audit_repo.count_by_action.return_value = {}

        result = await audit_service.get_stats()

        assert result.total == 0


@pytest.mark.unit
class TestAuditServiceGetByResource:
    @pytest.mark.asyncio
    async def test_get_by_resource_success(
        self,
        mock_audit_repo: AsyncMock,
        audit_service: AuditService,
    ) -> None:
        logs = [make_audit_log(audit_log_id=i) for i in range(1, 3)]
        mock_audit_repo.get_by_resource.return_value = (logs, 2)

        result = await audit_service.get_by_resource("agent", "42")

        assert len(result.items) == 2
        assert result.total == 2
        mock_audit_repo.get_by_resource.assert_called_once_with(
            "agent", "42", page=1, page_size=20,
        )
