"""Insights 模块测试配置和 Fixture。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.insights.application.services.insights_service import InsightsService
from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.modules.insights.domain.repositories.usage_record_repository import (
    IUsageRecordRepository,
)
from src.shared.domain.constants import MODEL_CLAUDE_SONNET_46


def make_usage_record(
    *,
    record_id: int = 1,
    user_id: int = 10,
    agent_id: int = 5,
    conversation_id: int | None = 100,
    model_id: str = MODEL_CLAUDE_SONNET_46,
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
def insights_service(
    mock_usage_repo: AsyncMock,
) -> InsightsService:
    """InsightsService 实例（注入所有 mock 依赖）。"""
    return InsightsService(
        usage_repo=mock_usage_repo,
    )
