"""Insights API 端点集成测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.insights.api.dependencies import get_insights_service
from src.modules.insights.application.dto.insights_dto import (
    UsageRecordDTO,
    UsageSummaryDTO,
)
from src.modules.insights.domain.exceptions import (
    UsageRecordNotFoundError,
)
from src.presentation.api.main import create_app
from src.shared.application.dtos import PagedResult


def _now() -> datetime:
    return datetime.now(UTC)


def _make_user(role: str = "developer", user_id: int = 1) -> UserDTO:
    return UserDTO(id=user_id, email="test@example.com", name="Test", role=role, is_active=True)


def _make_record_dto(record_id: int = 1) -> UsageRecordDTO:
    now = _now()
    return UsageRecordDTO(
        id=record_id,
        user_id=1,
        agent_id=5,
        conversation_id=100,
        model_id="anthropic.claude-sonnet-4-20250514",
        tokens_input=1000,
        tokens_output=500,
        estimated_cost=0.0105,
        recorded_at=now,
        created_at=now,
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(mock_service: AsyncMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    app.dependency_overrides[get_insights_service] = lambda: mock_service
    yield TestClient(app)  # type: ignore[misc]
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(mock_service: AsyncMock) -> TestClient:
    """ADMIN 用户客户端。"""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _make_user(role="admin")
    app.dependency_overrides[get_insights_service] = lambda: mock_service
    yield TestClient(app)  # type: ignore[misc]
    app.dependency_overrides.clear()


# ── 使用记录列表端点 ──


@pytest.mark.integration
class TestListUsageRecordsEndpoint:
    """GET /api/v1/insights/usage-records 测试。"""

    def test_list_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_usage_records.return_value = PagedResult(
            items=[_make_record_dto()], total=1, page=1, page_size=20,
        )
        resp = client.get("/api/v1/insights/usage-records")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_list_with_pagination(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_usage_records.return_value = PagedResult(
            items=[], total=0, page=2, page_size=10,
        )
        resp = client.get("/api/v1/insights/usage-records?page=2&page_size=10")
        assert resp.status_code == 200

    def test_list_invalid_page_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/insights/usage-records?page=0")
        assert resp.status_code == 422

    def test_non_admin_forced_user_filter(
        self, client: TestClient, mock_service: AsyncMock,
    ) -> None:
        """非 ADMIN 用户请求时，user_id 被强制为当前用户 ID。"""
        mock_service.list_usage_records.return_value = PagedResult(
            items=[], total=0, page=1, page_size=20,
        )
        # 即使传入 user_id=99, 非 admin 用户也应被强制过滤为自己的 id
        resp = client.get("/api/v1/insights/usage-records?user_id=99")
        assert resp.status_code == 200
        # 验证 service 被调用时 user_id=1 (当前用户)
        call_kwargs = mock_service.list_usage_records.call_args
        assert call_kwargs.kwargs["user_id"] == 1

    def test_admin_can_filter_any_user(
        self, admin_client: TestClient, mock_service: AsyncMock,
    ) -> None:
        """ADMIN 用户可以按任意 user_id 过滤。"""
        mock_service.list_usage_records.return_value = PagedResult(
            items=[], total=0, page=1, page_size=20,
        )
        resp = admin_client.get("/api/v1/insights/usage-records?user_id=99")
        assert resp.status_code == 200
        call_kwargs = mock_service.list_usage_records.call_args
        assert call_kwargs.kwargs["user_id"] == 99


# ── 使用记录详情端点 ──


@pytest.mark.integration
class TestGetUsageRecordEndpoint:
    """GET /api/v1/insights/usage-records/{id} 测试。"""

    def test_get_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_usage_record.return_value = _make_record_dto(record_id=42)
        resp = client.get("/api/v1/insights/usage-records/42")
        assert resp.status_code == 200
        assert resp.json()["id"] == 42

    def test_get_not_found_returns_404(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_usage_record.side_effect = UsageRecordNotFoundError(record_id=999)
        resp = client.get("/api/v1/insights/usage-records/999")
        assert resp.status_code == 404


# ── 使用量摘要端点 ──


@pytest.mark.integration
class TestUsageSummaryEndpoint:
    """GET /api/v1/insights/usage-summary (旧接口) 测试。"""

    def test_summary_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_usage_summary.return_value = UsageSummaryDTO(
            total_tokens=15000,
            total_cost=0.05,
            conversation_count=10,
            record_count=25,
            period="daily",
        )
        resp = client.get("/api/v1/insights/usage-summary?period=daily")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_tokens"] == 15000
        assert data["total_cost"] == 0.05
        assert data["period"] == "daily"

    def test_summary_with_date_filter(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_usage_summary.return_value = UsageSummaryDTO(
            total_tokens=0, total_cost=0.0, conversation_count=0, record_count=0, period="all",
        )
        resp = client.get(
            "/api/v1/insights/usage-summary"
            "?start_date=2025-01-01T00:00:00Z&end_date=2025-06-01T00:00:00Z",
        )
        assert resp.status_code == 200

    def test_summary_non_admin_forced_user(
        self, client: TestClient, mock_service: AsyncMock,
    ) -> None:
        """非 ADMIN 用户的 usage-summary 请求被强制过滤为自己。"""
        mock_service.get_usage_summary.return_value = UsageSummaryDTO(
            total_tokens=0, total_cost=0.0, conversation_count=0, record_count=0, period="all",
        )
        resp = client.get("/api/v1/insights/usage-summary?user_id=99")
        assert resp.status_code == 200
        call_kwargs = mock_service.get_usage_summary.call_args
        assert call_kwargs.kwargs["user_id"] == 1


# ── 未认证访问 ──


@pytest.mark.integration
class TestUnauthenticatedAccess:
    """未认证访问测试。"""

    def test_unauthenticated_returns_401(self, mock_service: AsyncMock) -> None:
        """未提供认证信息时返回 401。"""
        app = create_app()
        # 不覆盖 get_current_user, 使用真实认证
        app.dependency_overrides[get_insights_service] = lambda: mock_service
        unauthenticated_client = TestClient(app)

        resp = unauthenticated_client.get("/api/v1/insights/usage-records")
        assert resp.status_code == 401
