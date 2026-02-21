"""Insights 聚合一致性测试 — 验证 Service 返回的聚合结果与手动计算一致。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.insights.application.services.insights_service import InsightsService
from src.modules.insights.domain.repositories.usage_record_repository import (
    IUsageRecordRepository,
)
from src.modules.insights.domain.value_objects.agent_token_breakdown import (
    AgentTokenBreakdown,
)
from src.modules.insights.domain.value_objects.daily_usage_trend import DailyUsageTrend


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=IUsageRecordRepository)


def _make_service(repo: AsyncMock) -> InsightsService:
    return InsightsService(usage_repo=repo)


# ── 原始使用记录数据 ──

# 模拟 3 个 Agent 的使用记录 (手动 sum 基准)
_AGENT_RECORDS = {
    1: {"name": "Agent-A", "tokens_input": 3000, "tokens_output": 2000, "count": 10},
    2: {"name": "Agent-B", "tokens_input": 1500, "tokens_output": 800, "count": 5},
    3: {"name": "Agent-C", "tokens_input": 500, "tokens_output": 200, "count": 2},
}

# 模拟跨 3 天的使用记录 (手动按日 sum 基准)
_DAILY_RECORDS = {
    "2025-06-01": {"count": 8, "tokens_input": 2000, "tokens_output": 1000, "users": 3},
    "2025-06-02": {"count": 5, "tokens_input": 1500, "tokens_output": 600, "users": 2},
    "2025-06-03": {"count": 4, "tokens_input": 1000, "tokens_output": 400, "users": 2},
}


@pytest.mark.unit
class TestCostBreakdownConsistency:
    """验证 get_cost_breakdown 返回的 per-agent 聚合值与手动 sum 一致。"""

    @pytest.mark.asyncio
    async def test_cost_breakdown_matches_usage_records(self, mock_repo: AsyncMock) -> None:
        """每个 Agent 的 total_tokens = tokens_input + tokens_output, 总聚合 = 各 Agent 之和。"""
        # Arrange: 构建 Repository 返回的聚合结果 (模拟 SQL GROUP BY agent_id)
        breakdowns = [
            AgentTokenBreakdown(
                agent_id=aid,
                agent_name=data["name"],
                total_tokens=data["tokens_input"] + data["tokens_output"],
                tokens_input=data["tokens_input"],
                tokens_output=data["tokens_output"],
                invocation_count=data["count"],
            )
            for aid, data in _AGENT_RECORDS.items()
        ]
        mock_repo.get_cost_breakdown_by_agent.return_value = breakdowns
        service = _make_service(mock_repo)

        start = datetime(2025, 6, 1, tzinfo=UTC)
        end = datetime(2025, 6, 30, tzinfo=UTC)

        # Act
        result = await service.get_cost_breakdown(start=start, end=end)

        # Assert: 逐 Agent 校验 total_tokens = input + output
        for breakdown in result:
            assert breakdown.total_tokens == breakdown.tokens_input + breakdown.tokens_output, (
                f"Agent {breakdown.agent_id}: total_tokens({breakdown.total_tokens}) "
                f"!= input({breakdown.tokens_input}) + output({breakdown.tokens_output})"
            )

        # Assert: 全局聚合一致性 (手动 sum 与 result sum 匹配)
        expected_total_tokens = sum(d["tokens_input"] + d["tokens_output"] for d in _AGENT_RECORDS.values())
        actual_total_tokens = sum(b.total_tokens for b in result)
        assert actual_total_tokens == expected_total_tokens

        expected_total_invocations = sum(d["count"] for d in _AGENT_RECORDS.values())
        actual_total_invocations = sum(b.invocation_count for b in result)
        assert actual_total_invocations == expected_total_invocations

    @pytest.mark.asyncio
    async def test_cost_breakdown_single_agent(self, mock_repo: AsyncMock) -> None:
        """单 Agent 场景: 聚合结果唯一且值正确。"""
        mock_repo.get_cost_breakdown_by_agent.return_value = [
            AgentTokenBreakdown(
                agent_id=1,
                agent_name="Solo",
                total_tokens=7000,
                tokens_input=4000,
                tokens_output=3000,
                invocation_count=20,
            ),
        ]
        service = _make_service(mock_repo)

        result = await service.get_cost_breakdown(
            start=datetime(2025, 6, 1, tzinfo=UTC),
            end=datetime(2025, 6, 30, tzinfo=UTC),
        )

        assert len(result) == 1
        assert result[0].total_tokens == 4000 + 3000
        assert result[0].invocation_count == 20

    @pytest.mark.asyncio
    async def test_cost_breakdown_empty(self, mock_repo: AsyncMock) -> None:
        """无数据时返回空列表。"""
        mock_repo.get_cost_breakdown_by_agent.return_value = []
        service = _make_service(mock_repo)

        result = await service.get_cost_breakdown(
            start=datetime(2025, 6, 1, tzinfo=UTC),
            end=datetime(2025, 6, 30, tzinfo=UTC),
        )

        assert result == []


@pytest.mark.unit
class TestUsageTrendsConsistency:
    """验证 get_usage_trends 返回的日维度聚合与手动按日 sum 一致。"""

    @pytest.mark.asyncio
    async def test_usage_trends_matches_usage_records(self, mock_repo: AsyncMock) -> None:
        """跨 3 天的 UsageRecord, 验证日维度聚合 total_tokens 与手动按日 sum 一致。"""
        # Arrange: 构建 Repository 返回的日聚合结果 (模拟 SQL GROUP BY date)
        trends = [
            DailyUsageTrend(
                date=date,
                invocation_count=data["count"],
                total_tokens=data["tokens_input"] + data["tokens_output"],
                unique_users=data["users"],
            )
            for date, data in _DAILY_RECORDS.items()
        ]
        mock_repo.get_daily_usage_trends.return_value = trends
        service = _make_service(mock_repo)

        start = datetime(2025, 6, 1, tzinfo=UTC)
        end = datetime(2025, 6, 3, tzinfo=UTC)

        # Act
        result = await service.get_usage_trends(start=start, end=end)

        # Assert: 验证天数
        assert len(result) == 3

        # Assert: 逐日校验 total_tokens = 手动 sum(tokens_input + tokens_output)
        for trend in result:
            expected_data = _DAILY_RECORDS[trend.date]
            expected_tokens = expected_data["tokens_input"] + expected_data["tokens_output"]
            assert trend.total_tokens == expected_tokens, (
                f"日期 {trend.date}: total_tokens({trend.total_tokens}) != 预期({expected_tokens})"
            )
            assert trend.invocation_count == expected_data["count"]
            assert trend.unique_users == expected_data["users"]

        # Assert: 全局聚合一致性
        expected_total = sum(d["tokens_input"] + d["tokens_output"] for d in _DAILY_RECORDS.values())
        actual_total = sum(t.total_tokens for t in result)
        assert actual_total == expected_total

        expected_total_invocations = sum(d["count"] for d in _DAILY_RECORDS.values())
        actual_total_invocations = sum(t.invocation_count for t in result)
        assert actual_total_invocations == expected_total_invocations

    @pytest.mark.asyncio
    async def test_usage_trends_single_day(self, mock_repo: AsyncMock) -> None:
        """单日场景: 聚合结果唯一且值正确。"""
        mock_repo.get_daily_usage_trends.return_value = [
            DailyUsageTrend(
                date="2025-06-15",
                invocation_count=12,
                total_tokens=5000,
                unique_users=4,
            ),
        ]
        service = _make_service(mock_repo)

        result = await service.get_usage_trends(
            start=datetime(2025, 6, 15, tzinfo=UTC),
            end=datetime(2025, 6, 15, tzinfo=UTC),
        )

        assert len(result) == 1
        assert result[0].date == "2025-06-15"
        assert result[0].total_tokens == 5000
        assert result[0].invocation_count == 12

    @pytest.mark.asyncio
    async def test_usage_trends_empty(self, mock_repo: AsyncMock) -> None:
        """无数据时返回空列表。"""
        mock_repo.get_daily_usage_trends.return_value = []
        service = _make_service(mock_repo)

        result = await service.get_usage_trends(
            start=datetime(2025, 6, 1, tzinfo=UTC),
            end=datetime(2025, 6, 30, tzinfo=UTC),
        )

        assert result == []
