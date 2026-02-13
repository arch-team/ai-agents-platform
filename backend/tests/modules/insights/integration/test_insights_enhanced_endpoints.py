"""Insights 增强端点集成测试 — cost-breakdown / usage-trends / summary。"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.insights.api.dependencies import get_insights_service
from src.modules.insights.application.dto.insights_dto import InsightsSummaryDTO
from src.modules.insights.domain.value_objects.agent_token_breakdown import (
    AgentTokenBreakdown,
)
from src.modules.insights.domain.value_objects.daily_usage_trend import DailyUsageTrend
from src.presentation.api.main import create_app


def _make_user(role: str = "admin", user_id: int = 1) -> UserDTO:
    return UserDTO(id=user_id, email="test@example.com", name="Test", role=role, is_active=True)


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


# ── GET /cost-breakdown ──


@pytest.mark.integration
class TestCostBreakdownEndpoint:
    """GET /api/v1/insights/cost-breakdown 端点测试。"""

    def test_returns_agent_token_breakdowns(self, client: TestClient, mock_service: AsyncMock) -> None:
        """正常返回: 按 Agent 维度 Token 消耗聚合。"""
        # Arrange
        mock_service.get_cost_breakdown.return_value = [
            AgentTokenBreakdown(
                agent_id=1, agent_name="Agent-A",
                total_tokens=5000, tokens_input=3000, tokens_output=2000,
                invocation_count=10,
            ),
            AgentTokenBreakdown(
                agent_id=2, agent_name="Agent-B",
                total_tokens=3000, tokens_input=2000, tokens_output=1000,
                invocation_count=5,
            ),
        ]

        # Act
        resp = client.get("/api/v1/insights/cost-breakdown?start_date=2025-06-01&end_date=2025-06-30")

        # Assert
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total_tokens"] == 8000
        assert data["items"][0]["agent_id"] == 1
        assert data["items"][0]["agent_name"] == "Agent-A"
        assert data["items"][0]["total_tokens"] == 5000
        assert data["items"][0]["tokens_input"] == 3000
        assert data["items"][0]["tokens_output"] == 2000
        assert data["items"][0]["invocation_count"] == 10
        assert data["period"]["start_date"] == "2025-06-01"
        assert data["period"]["end_date"] == "2025-06-30"

    def test_empty_breakdown(self, client: TestClient, mock_service: AsyncMock) -> None:
        """空数据: 无 Agent 消耗记录时返回空列表。"""
        mock_service.get_cost_breakdown.return_value = []

        resp = client.get("/api/v1/insights/cost-breakdown")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_tokens"] == 0

    def test_default_date_range(self, client: TestClient, mock_service: AsyncMock) -> None:
        """不传日期参数时使用默认最近 30 天范围。"""
        mock_service.get_cost_breakdown.return_value = []

        resp = client.get("/api/v1/insights/cost-breakdown")
        assert resp.status_code == 200
        # 验证 service 被调用时有 start 和 end 参数
        call_args = mock_service.get_cost_breakdown.call_args
        start = call_args.kwargs["start"]
        end = call_args.kwargs["end"]
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        # 范围大约 30 天
        delta = end - start
        assert 29 <= delta.days <= 31


# ── GET /usage-trends ──


@pytest.mark.integration
class TestUsageTrendsEndpoint:
    """GET /api/v1/insights/usage-trends 端点测试。"""

    def test_returns_daily_trends(self, client: TestClient, mock_service: AsyncMock) -> None:
        """正常返回: 日维度使用趋势。"""
        # Arrange
        mock_service.get_usage_trends.return_value = [
            DailyUsageTrend(date="2025-06-01", invocation_count=50, total_tokens=10000, unique_users=5),
            DailyUsageTrend(date="2025-06-02", invocation_count=30, total_tokens=6000, unique_users=3),
        ]

        # Act
        resp = client.get("/api/v1/insights/usage-trends?start_date=2025-06-01&end_date=2025-06-03")

        # Assert
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data_points"]) == 2
        assert data["data_points"][0]["date"] == "2025-06-01"
        assert data["data_points"][0]["invocation_count"] == 50
        assert data["data_points"][0]["total_tokens"] == 10000
        assert data["data_points"][0]["unique_users"] == 5
        assert data["period"]["start_date"] == "2025-06-01"
        assert data["period"]["end_date"] == "2025-06-03"

    def test_empty_trends(self, client: TestClient, mock_service: AsyncMock) -> None:
        """空数据: 无趋势记录时返回空列表。"""
        mock_service.get_usage_trends.return_value = []

        resp = client.get("/api/v1/insights/usage-trends")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data_points"] == []


# ── GET /summary (增强版) ──


@pytest.mark.integration
class TestEnhancedSummaryEndpoint:
    """GET /api/v1/insights/summary 增强端点测试。"""

    def test_returns_insights_summary(self, client: TestClient, mock_service: AsyncMock) -> None:
        """正常返回: 含 Cost Explorer 总成本和 Token 聚合。"""
        # Arrange
        mock_service.get_insights_summary.return_value = InsightsSummaryDTO(
            total_agents=3, active_agents=3, total_invocations=50, total_cost=45.67, total_tokens=20000,
        )

        # Act
        resp = client.get("/api/v1/insights/summary?start_date=2025-06-01&end_date=2025-06-30")

        # Assert
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_agents"] == 3
        assert data["active_agents"] == 3
        assert data["total_invocations"] == 50
        assert data["total_cost"] == 45.67
        assert data["total_tokens"] == 20000
        assert data["period"]["start_date"] == "2025-06-01"
        assert data["period"]["end_date"] == "2025-06-30"

    def test_summary_with_zero_cost(self, client: TestClient, mock_service: AsyncMock) -> None:
        """Cost Explorer 降级时 total_cost 为 0.0。"""
        mock_service.get_insights_summary.return_value = InsightsSummaryDTO(
            total_agents=1, active_agents=1, total_invocations=10, total_cost=0.0, total_tokens=5000,
        )

        resp = client.get("/api/v1/insights/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cost"] == 0.0
        assert data["total_tokens"] == 5000

    def test_summary_default_date_range(self, client: TestClient, mock_service: AsyncMock) -> None:
        """不传日期参数时使用默认最近 30 天范围。"""
        mock_service.get_insights_summary.return_value = InsightsSummaryDTO(
            total_agents=0, active_agents=0, total_invocations=0, total_cost=0.0, total_tokens=0,
        )

        resp = client.get("/api/v1/insights/summary")
        assert resp.status_code == 200
        call_args = mock_service.get_insights_summary.call_args
        start = call_args.kwargs["start"]
        end = call_args.kwargs["end"]
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
