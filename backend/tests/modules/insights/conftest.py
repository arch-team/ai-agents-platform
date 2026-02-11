"""Insights 模块测试配置和 Fixture。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.insights.application.interfaces.cost_calculator import ICostCalculator
from src.modules.insights.application.services.insights_service import InsightsService
from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.modules.insights.domain.repositories.usage_record_repository import (
    IUsageRecordRepository,
)
from src.modules.insights.domain.value_objects.cost_breakdown import CostBreakdown


def make_usage_record(
    *,
    record_id: int = 1,
    user_id: int = 10,
    agent_id: int = 5,
    conversation_id: int = 100,
    model_id: str = "anthropic.claude-sonnet-4-20250514",
    tokens_input: int = 1000,
    tokens_output: int = 500,
    estimated_cost: float = 0.0105,
) -> UsageRecord:
    """创建测试用 UsageRecord 实体。"""
    record = UsageRecord(
        user_id=user_id,
        agent_id=agent_id,
        conversation_id=conversation_id,
        model_id=model_id,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        estimated_cost=estimated_cost,
    )
    object.__setattr__(record, "id", record_id)
    return record


@pytest.fixture
def mock_usage_repo() -> AsyncMock:
    """UsageRecord 仓库 Mock。"""
    return AsyncMock(spec=IUsageRecordRepository)


@pytest.fixture
def mock_cost_calculator() -> MagicMock:
    """ICostCalculator Mock。"""
    calc = MagicMock(spec=ICostCalculator)
    calc.calculate_cost.return_value = CostBreakdown(
        tokens_input=1000,
        tokens_output=500,
        input_cost=0.003,
        output_cost=0.0075,
        total_cost=0.0105,
        model_id="anthropic.claude-sonnet-4-20250514",
    )
    return calc


@pytest.fixture
def insights_service(
    mock_usage_repo: AsyncMock,
    mock_cost_calculator: MagicMock,
) -> InsightsService:
    """InsightsService 实例（注入所有 mock 依赖）。"""
    return InsightsService(
        usage_repo=mock_usage_repo,
        cost_calculator=mock_cost_calculator,
    )
