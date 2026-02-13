"""成本计算器接口。

已弃用: 平台总成本改用 AWS Cost Explorer (ICostExplorer)，
estimated_cost 固定为 0.0。保留此接口仅用于向后兼容。
"""

from abc import ABC, abstractmethod

from src.modules.insights.domain.value_objects.cost_breakdown import CostBreakdown


class ICostCalculator(ABC):
    """成本计算器抽象接口 — 根据模型和 token 数计算成本。"""

    @abstractmethod
    def calculate_cost(
        self,
        model_id: str,
        tokens_input: int,
        tokens_output: int,
    ) -> CostBreakdown:
        """计算指定模型和 token 数的成本明细。"""
