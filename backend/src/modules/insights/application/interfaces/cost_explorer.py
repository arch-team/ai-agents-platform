"""AWS Cost Explorer 接口 — 获取平台真实 Bedrock 成本。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DailyCostPoint:
    """单日成本数据点。"""

    date: str
    amount: float
    currency: str = "USD"


@dataclass(frozen=True)
class PlatformCostSummary:
    """平台 Bedrock 成本汇总。"""

    total_cost: float
    currency: str
    daily_costs: tuple[DailyCostPoint, ...]
    start_date: str
    end_date: str


class ICostExplorer(ABC):
    """AWS Cost Explorer 抽象接口 — 查询平台 Bedrock 实际账单。"""

    @abstractmethod
    async def get_bedrock_cost(self, start_date: str, end_date: str) -> PlatformCostSummary:
        """获取指定日期范围内的 Bedrock 服务成本。

        Raises:
            ExternalServiceError: Cost Explorer API 调用失败
        """
