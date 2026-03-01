"""AWS Cost Explorer 适配器 — boto3 ce client 薄封装。"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

import boto3
import structlog

from src.modules.insights.application.interfaces.cost_explorer import (
    DailyCostPoint,
    ICostExplorer,
    PlatformCostSummary,
)


logger = structlog.get_logger(__name__)


@lru_cache
def _get_ce_client() -> Any:
    """创建 Cost Explorer client 单例 (固定 us-east-1)。"""
    return boto3.client("ce", region_name="us-east-1")


class CostExplorerAdapter(ICostExplorer):
    """AWS Cost Explorer 薄封装 — 查询 Bedrock 服务实际账单。"""

    async def get_bedrock_cost(self, start_date: str, end_date: str) -> PlatformCostSummary:
        """查询指定日期范围的 Bedrock 成本 (get_cost_and_usage)。"""
        try:
            response: dict[str, Any] = await asyncio.to_thread(
                self._fetch_cost,
                start_date,
                end_date,
            )
        except Exception:
            logger.exception("cost_explorer_api_failed", start_date=start_date, end_date=end_date)
            # 降级: 返回零成本, 不阻断业务
            return PlatformCostSummary(
                total_cost=0.0,
                currency="USD",
                daily_costs=(),
                start_date=start_date,
                end_date=end_date,
            )

        daily_costs: list[DailyCostPoint] = []
        total = 0.0
        for result in response.get("ResultsByTime", []):
            date = result["TimePeriod"]["Start"]
            amount = float(result["Total"]["UnblendedCost"]["Amount"])
            currency = result["Total"]["UnblendedCost"]["Unit"]
            daily_costs.append(DailyCostPoint(date=date, amount=amount, currency=currency))
            total += amount

        return PlatformCostSummary(
            total_cost=round(total, 4),
            currency="USD",
            daily_costs=tuple(daily_costs),
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def _fetch_cost(start_date: str, end_date: str) -> dict[str, Any]:
        """同步调用 Cost Explorer API。"""
        client = _get_ce_client()
        result: dict[str, Any] = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            Filter={
                "Dimensions": {
                    "Key": "SERVICE",
                    "Values": ["Amazon Bedrock"],
                },
            },
        )
        return result
