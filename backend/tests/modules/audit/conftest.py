"""审计模块测试配置和 Fixture。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.modules.audit.application.services.audit_service import AuditService
from src.modules.audit.domain.entities.audit_log import AuditAction, AuditCategory, AuditLog
from src.modules.audit.domain.repositories.audit_log_repository import IAuditLogRepository


def make_audit_log(
    *,
    audit_log_id: int = 1,
    actor_id: int = 100,
    actor_name: str = "测试用户",
    action: AuditAction = AuditAction.CREATE,
    category: AuditCategory = AuditCategory.AGENT_MANAGEMENT,
    resource_type: str = "agent",
    resource_id: str = "42",
    resource_name: str | None = "测试 Agent",
    module: str = "agents",
    ip_address: str | None = "127.0.0.1",
    user_agent: str | None = None,
    request_method: str | None = "POST",
    request_path: str | None = "/api/v1/agents",
    status_code: int | None = 201,
    result: str = "success",
    error_message: str | None = None,
    details: dict[str, str | int | float | bool | None] | None = None,
    occurred_at: datetime | None = None,
) -> AuditLog:
    """创建测试用 AuditLog 实体。"""
    return AuditLog(
        id=audit_log_id,
        actor_id=actor_id,
        actor_name=actor_name,
        action=action,
        category=category,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        module=module,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
        status_code=status_code,
        result=result,
        error_message=error_message,
        details=details,
        occurred_at=occurred_at or datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def mock_audit_repo() -> AsyncMock:
    """AuditLog 仓库 Mock。"""
    return AsyncMock(spec=IAuditLogRepository)


@pytest.fixture
def audit_service(mock_audit_repo: AsyncMock) -> AuditService:
    """AuditService 实例（注入 mock 仓库）。"""
    return AuditService(mock_audit_repo)


@pytest.fixture
def mock_event_bus():  # type: ignore[no-untyped-def]
    """Mock event_bus，自动 patch AuditService 中的 event_bus。"""
    with patch(
        "src.modules.audit.application.services.audit_service.event_bus"
    ) as mock_bus:
        mock_bus.publish_async = AsyncMock()
        yield mock_bus
