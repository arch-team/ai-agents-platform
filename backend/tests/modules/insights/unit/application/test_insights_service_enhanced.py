"""InsightsService 增强方法单元测试 — get_cost_breakdown / get_usage_trends / get_insights_summary。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.insights.application.dto.insights_dto import InsightsSummaryDTO
from src.modules.insights.application.interfaces.cost_explorer import (
    ICostExplorer,
    PlatformCostSummary,
)
from src.modules.insights.application.services.insights_service import InsightsService
from src.modules.insights.domain.exceptions import InvalidDateRangeError
from src.modules.insights.domain.repositories.usage_record_repository import (
    IUsageRecordRepository,
)
from src.modules.insights.domain.value_objects.agent_token_breakdown import (
    AgentTokenBreakdown,
)
from src.modules.insights.domain.value_objects.aggregated_stats import AggregatedStats
from src.modules.insights.domain.value_objects.daily_usage_trend import DailyUsageTrend


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=IUsageRecordRepository)


@pytest.fixture
def mock_explorer() -> AsyncMock:
    return AsyncMock(spec=ICostExplorer)


def _make_service(
    repo: AsyncMock,
    explorer: AsyncMock | None = None,
) -> InsightsService:
    return InsightsService(usage_repo=repo, cost_explorer=explorer)


# ── get_cost_breakdown ──


@pytest.mark.unit
class TestGetCostBreakdown:
    """get_cost_breakdown 测试。"""

    @pytest.mark.asyncio
    async def test_returns_agent_token_breakdowns(self, mock_repo: AsyncMock) -> None:
        """正常返回: 代理 Repository 聚合结果。"""
        # Arrange
        expected = [
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
        mock_repo.get_cost_breakdown_by_agent.return_value = expected
        service = _make_service(mock_repo)

        start = datetime(2025, 6, 1, tzinfo=UTC)
        end = datetime(2025, 6, 30, tzinfo=UTC)

        # Act
        result = await service.get_cost_breakdown(start=start, end=end)

        # Assert
        assert result == expected
        mock_repo.get_cost_breakdown_by_agent.assert_called_once_with(start=start, end=end)

    @pytest.mark.asyncio
    async def test_invalid_date_range_raises(self, mock_repo: AsyncMock) -> None:
        """日期范围无效时抛出 InvalidDateRangeError。"""
        service = _make_service(mock_repo)
        start = datetime(2025, 7, 1, tzinfo=UTC)
        end = datetime(2025, 6, 1, tzinfo=UTC)

        with pytest.raises(InvalidDateRangeError):
            await service.get_cost_breakdown(start=start, end=end)


# ── get_usage_trends ──


@pytest.mark.unit
class TestGetUsageTrends:
    """get_usage_trends 测试。"""

    @pytest.mark.asyncio
    async def test_returns_daily_trends(self, mock_repo: AsyncMock) -> None:
        """正常返回: 代理 Repository 日维度聚合结果。"""
        # Arrange
        expected = [
            DailyUsageTrend(date="2025-06-01", invocation_count=50, total_tokens=10000, unique_users=5),
            DailyUsageTrend(date="2025-06-02", invocation_count=30, total_tokens=6000, unique_users=3),
        ]
        mock_repo.get_daily_usage_trends.return_value = expected
        service = _make_service(mock_repo)

        start = datetime(2025, 6, 1, tzinfo=UTC)
        end = datetime(2025, 6, 3, tzinfo=UTC)

        # Act
        result = await service.get_usage_trends(start=start, end=end)

        # Assert
        assert result == expected
        mock_repo.get_daily_usage_trends.assert_called_once_with(start=start, end=end)

    @pytest.mark.asyncio
    async def test_invalid_date_range_raises(self, mock_repo: AsyncMock) -> None:
        """日期范围无效时抛出 InvalidDateRangeError。"""
        service = _make_service(mock_repo)
        start = datetime(2025, 7, 1, tzinfo=UTC)
        end = datetime(2025, 6, 1, tzinfo=UTC)

        with pytest.raises(InvalidDateRangeError):
            await service.get_usage_trends(start=start, end=end)


# ── get_insights_summary ──


@pytest.mark.unit
class TestGetInsightsSummary:
    """get_insights_summary 测试。"""

    @pytest.mark.asyncio
    async def test_returns_summary_with_cost_explorer(
        self, mock_repo: AsyncMock, mock_explorer: AsyncMock,
    ) -> None:
        """正常返回: 含 CostExplorer 真实成本。"""
        # Arrange
        mock_repo.get_aggregated_stats.return_value = AggregatedStats(
            total_tokens=20000, total_cost=0.0, conversation_count=10, record_count=50,
        )
        mock_repo.count_distinct_agents.return_value = 3
        mock_explorer.get_bedrock_cost.return_value = PlatformCostSummary(
            total_cost=45.67, currency="USD", daily_costs=(), start_date="2025-06-01", end_date="2025-06-30",
        )
        service = _make_service(mock_repo, mock_explorer)

        start = datetime(2025, 6, 1, tzinfo=UTC)
        end = datetime(2025, 6, 30, tzinfo=UTC)

        # Act
        result = await service.get_insights_summary(start=start, end=end)

        # Assert
        assert isinstance(result, InsightsSummaryDTO)
        assert result.total_agents == 3
        assert result.active_agents == 3
        assert result.total_invocations == 50
        assert result.total_cost == 45.67
        assert result.total_tokens == 20000

    @pytest.mark.asyncio
    async def test_returns_summary_without_cost_explorer(
        self, mock_repo: AsyncMock,
    ) -> None:
        """无 CostExplorer 时降级: total_cost 为 0.0。"""
        # Arrange
        mock_repo.get_aggregated_stats.return_value = AggregatedStats(
            total_tokens=10000, total_cost=0.0, conversation_count=5, record_count=20,
        )
        mock_repo.count_distinct_agents.return_value = 2
        service = _make_service(mock_repo, explorer=None)

        start = datetime(2025, 6, 1, tzinfo=UTC)
        end = datetime(2025, 6, 30, tzinfo=UTC)

        # Act
        result = await service.get_insights_summary(start=start, end=end)

        # Assert
        assert result.total_cost == 0.0
        assert result.total_agents == 2
        assert result.total_invocations == 20
        assert result.total_tokens == 10000

    @pytest.mark.asyncio
    async def test_invalid_date_range_raises(
        self, mock_repo: AsyncMock,
    ) -> None:
        """日期范围无效时抛出 InvalidDateRangeError。"""
        service = _make_service(mock_repo)
        start = datetime(2025, 7, 1, tzinfo=UTC)
        end = datetime(2025, 6, 1, tzinfo=UTC)

        with pytest.raises(InvalidDateRangeError):
            await service.get_insights_summary(start=start, end=end)
