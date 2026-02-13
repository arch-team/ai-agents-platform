"""Insights API 依赖注入。"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insights.application.interfaces.cost_calculator import ICostCalculator
from src.modules.insights.application.interfaces.cost_explorer import ICostExplorer
from src.modules.insights.application.services.insights_service import InsightsService
from src.modules.insights.infrastructure.external.bedrock_cost_calculator import (
    BedrockCostCalculator,
)
from src.modules.insights.infrastructure.external.cost_explorer_adapter import (
    CostExplorerAdapter,
)
from src.modules.insights.infrastructure.persistence.repositories.usage_record_repository_impl import (
    UsageRecordRepositoryImpl,
)
from src.shared.infrastructure.database import get_db


@lru_cache
def get_cost_calculator() -> ICostCalculator:
    """创建 BedrockCostCalculator 单例 (已弃用 — 仅保留向后兼容)。"""
    return BedrockCostCalculator()


@lru_cache
def get_cost_explorer() -> ICostExplorer:
    """创建 CostExplorerAdapter 单例。"""
    return CostExplorerAdapter()


async def get_insights_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InsightsService:
    """创建 InsightsService 实例。"""
    return InsightsService(
        usage_repo=UsageRecordRepositoryImpl(session=session),
        cost_calculator=get_cost_calculator(),
        cost_explorer=get_cost_explorer(),
    )
