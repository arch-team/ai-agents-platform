"""审计 API 端点集成测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.audit.api.dependencies import get_audit_service
from src.modules.audit.application.dto.audit_log_dto import AuditLogDTO, AuditStatsDTO
from src.modules.audit.domain.exceptions import AuditNotFoundError
from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.presentation.api.main import create_app
from src.shared.application.dtos import PagedResult


def _make_admin_user(
    *,
    user_id: int = 1,
    email: str = "admin@example.com",
    name: str = "Admin",
    role: str = "admin",
    is_active: bool = True,
) -> UserDTO:
    return UserDTO(id=user_id, email=email, name=name, role=role, is_active=is_active)


def _make_developer_user() -> UserDTO:
    return UserDTO(id=2, email="dev@example.com", name="Developer", role="developer", is_active=True)


def _make_audit_log_dto(
    *,
    audit_log_id: int = 1,
    actor_id: int = 100,
    action: str = "create",
    category: str = "agent_management",
) -> AuditLogDTO:
    now = datetime.now(UTC)
    return AuditLogDTO(
        id=audit_log_id,
        actor_id=actor_id,
        actor_name="测试用户",
        action=action,
        category=category,
        resource_type="agent",
        resource_id="42",
        resource_name="测试 Agent",
        module="agents",
        ip_address="127.0.0.1",
        user_agent=None,
        request_method="POST",
        request_path="/api/v1/agents",
        status_code=201,
        result="success",
        error_message=None,
        details=None,
        occurred_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def admin_user() -> UserDTO:
    return _make_admin_user()


@pytest.fixture
def app(mock_service: AsyncMock, admin_user: UserDTO):
    test_app = create_app()
    test_app.dependency_overrides[get_audit_service] = lambda: mock_service
    test_app.dependency_overrides[get_current_user] = lambda: admin_user
    return test_app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.mark.integration
class TestListAuditLogsEndpoint:
    """GET /api/v1/audit-logs 测试。"""

    def test_list_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回分页列表。"""
        mock_service.list_filtered.return_value = PagedResult(
            items=[_make_audit_log_dto()],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/audit-logs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_list_empty(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 空列表。"""
        mock_service.list_filtered.return_value = PagedResult(
            items=[], total=0, page=1, page_size=20,
        )

        response = client.get("/api/v1/audit-logs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_with_filters(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 带筛选参数。"""
        mock_service.list_filtered.return_value = PagedResult(
            items=[], total=0, page=1, page_size=20,
        )

        response = client.get(
            "/api/v1/audit-logs?category=agent_management&action=create&page=2&page_size=10",
        )

        assert response.status_code == 200
        mock_service.list_filtered.assert_called_once()

    def test_list_requires_admin(self, mock_service: AsyncMock) -> None:
        """403 非 ADMIN 用户无权访问。"""
        test_app = create_app()
        test_app.dependency_overrides[get_audit_service] = lambda: mock_service
        test_app.dependency_overrides[get_current_user] = lambda: _make_developer_user()
        dev_client = TestClient(test_app)

        response = dev_client.get("/api/v1/audit-logs")

        assert response.status_code == 403


@pytest.mark.integration
class TestGetAuditLogEndpoint:
    """GET /api/v1/audit-logs/{id} 测试。"""

    def test_get_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回详情。"""
        mock_service.get_by_id.return_value = _make_audit_log_dto(audit_log_id=42)

        response = client.get("/api/v1/audit-logs/42")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 42
        assert data["action"] == "create"

    def test_get_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        """404 记录不存在。"""
        mock_service.get_by_id.side_effect = AuditNotFoundError(999)

        response = client.get("/api/v1/audit-logs/999")

        assert response.status_code == 404


@pytest.mark.integration
class TestAuditStatsEndpoint:
    """GET /api/v1/audit-logs/stats 测试。"""

    def test_stats_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回统计信息。"""
        mock_service.get_stats.return_value = AuditStatsDTO(
            by_category={"agent_management": 10, "execution": 5},
            by_action={"create": 8, "update": 7},
            total=15,
        )

        response = client.get("/api/v1/audit-logs/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert data["by_category"]["agent_management"] == 10

    def test_stats_with_date_range(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 带日期范围参数。"""
        mock_service.get_stats.return_value = AuditStatsDTO(total=0)

        response = client.get(
            "/api/v1/audit-logs/stats?start_date=2026-01-01T00:00:00&end_date=2026-02-01T00:00:00",
        )

        assert response.status_code == 200
        mock_service.get_stats.assert_called_once()


@pytest.mark.integration
class TestAuditLogByResourceEndpoint:
    """GET /api/v1/audit-logs/resource/{resource_type}/{resource_id} 测试。"""

    def test_by_resource_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 按资源查询。"""
        mock_service.get_by_resource.return_value = PagedResult(
            items=[_make_audit_log_dto()],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/audit-logs/resource/agent/42")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_by_resource_empty(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 空结果。"""
        mock_service.get_by_resource.return_value = PagedResult(
            items=[], total=0, page=1, page_size=20,
        )

        response = client.get("/api/v1/audit-logs/resource/agent/999")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


@pytest.mark.integration
class TestExportAuditLogsEndpoint:
    """GET /api/v1/audit-logs/export 测试。"""

    def test_export_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回 CSV 文件。"""
        mock_service.list_filtered.return_value = PagedResult(
            items=[_make_audit_log_dto()],
            total=1,
            page=1,
            page_size=10000,
        )

        response = client.get("/api/v1/audit-logs/export")

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "audit_logs.csv" in response.headers["content-disposition"]
        # 验证 CSV 内容包含表头和数据行
        content = response.content.decode("utf-8-sig")
        lines = content.strip().split("\n")
        assert len(lines) >= 2  # 表头 + 至少 1 行数据
        assert "id" in lines[0]  # 表头包含 id 字段

    def test_export_empty(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 空 CSV（只有表头）。"""
        mock_service.list_filtered.return_value = PagedResult(
            items=[], total=0, page=1, page_size=10000,
        )

        response = client.get("/api/v1/audit-logs/export")

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        lines = content.strip().split("\n")
        assert len(lines) == 1  # 只有表头


@pytest.mark.integration
class TestAuditEndpointRoutes:
    """路由注册验证。"""

    def test_audit_list_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/audit-logs" in routes

    def test_audit_detail_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/audit-logs/{audit_log_id}" in routes

    def test_audit_stats_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/audit-logs/stats" in routes

    def test_audit_resource_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/audit-logs/resource/{resource_type}/{resource_id}" in routes

    def test_audit_export_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/audit-logs/export" in routes
