"""Bedrock 模型成本计算器 — ICostCalculator 实现。"""

from src.modules.insights.application.interfaces.cost_calculator import ICostCalculator
from src.modules.insights.domain.value_objects.cost_breakdown import CostBreakdown


# 模型定价表 (美元/百万 Token) — Phase 2 MVP 硬编码
_PRICING: dict[str, tuple[float, float]] = {
    "anthropic.claude-sonnet": (3.0, 15.0),
    "anthropic.claude-haiku": (0.25, 1.25),
}

_DEFAULT_PRICING: tuple[float, float] = (3.0, 15.0)

_TOKENS_PER_MILLION = 1_000_000


class BedrockCostCalculator(ICostCalculator):
    """基于 Bedrock 模型定价表的成本计算器。"""

    def calculate_cost(
        self,
        model_id: str,
        tokens_input: int,
        tokens_output: int,
    ) -> CostBreakdown:
        """根据模型和 token 数计算成本。"""
        input_price, output_price = self._get_pricing(model_id)

        input_cost = (tokens_input / _TOKENS_PER_MILLION) * input_price
        output_cost = (tokens_output / _TOKENS_PER_MILLION) * output_price
        total_cost = input_cost + output_cost

        return CostBreakdown(
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model_id=model_id,
        )

    @staticmethod
    def _get_pricing(model_id: str) -> tuple[float, float]:
        """根据 model_id 查找定价，支持前缀匹配。"""
        for prefix, pricing in _PRICING.items():
            if model_id.startswith(prefix):
                return pricing
        return _DEFAULT_PRICING
