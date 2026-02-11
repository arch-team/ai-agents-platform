"""BedrockCostCalculator 单元测试。"""

import pytest

from src.modules.insights.domain.value_objects.cost_breakdown import CostBreakdown
from src.modules.insights.infrastructure.external.bedrock_cost_calculator import (
    BedrockCostCalculator,
)


@pytest.fixture
def calculator() -> BedrockCostCalculator:
    return BedrockCostCalculator()


@pytest.mark.unit
class TestBedrockCostCalculator:
    """BedrockCostCalculator 测试。"""

    def test_sonnet_pricing(self, calculator: BedrockCostCalculator) -> None:
        """Claude Sonnet 模型定价: input $3/MTok, output $15/MTok。"""
        result = calculator.calculate_cost(
            "anthropic.claude-sonnet-4-20250514",
            tokens_input=1_000_000,
            tokens_output=1_000_000,
        )
        assert isinstance(result, CostBreakdown)
        assert result.input_cost == pytest.approx(3.0)
        assert result.output_cost == pytest.approx(15.0)
        assert result.total_cost == pytest.approx(18.0)

    def test_haiku_pricing(self, calculator: BedrockCostCalculator) -> None:
        """Claude Haiku 模型定价: input $0.25/MTok, output $1.25/MTok。"""
        result = calculator.calculate_cost(
            "anthropic.claude-haiku-3-20240307",
            tokens_input=1_000_000,
            tokens_output=1_000_000,
        )
        assert result.input_cost == pytest.approx(0.25)
        assert result.output_cost == pytest.approx(1.25)
        assert result.total_cost == pytest.approx(1.5)

    def test_unknown_model_uses_default(self, calculator: BedrockCostCalculator) -> None:
        """未知模型使用默认定价。"""
        result = calculator.calculate_cost(
            "some-unknown-model",
            tokens_input=1_000_000,
            tokens_output=1_000_000,
        )
        assert result.input_cost == pytest.approx(3.0)
        assert result.output_cost == pytest.approx(15.0)

    def test_small_token_count(self, calculator: BedrockCostCalculator) -> None:
        """小量 token 计算。"""
        result = calculator.calculate_cost(
            "anthropic.claude-sonnet-4-20250514",
            tokens_input=1000,
            tokens_output=500,
        )
        # input: 1000/1M * $3 = $0.003
        # output: 500/1M * $15 = $0.0075
        assert result.input_cost == pytest.approx(0.003)
        assert result.output_cost == pytest.approx(0.0075)
        assert result.total_cost == pytest.approx(0.0105)

    def test_zero_tokens(self, calculator: BedrockCostCalculator) -> None:
        """零 token 数应返回零成本。"""
        result = calculator.calculate_cost("anthropic.claude-sonnet", 0, 0)
        assert result.total_cost == 0.0

    def test_preserves_model_id(self, calculator: BedrockCostCalculator) -> None:
        """结果应保留模型 ID。"""
        result = calculator.calculate_cost("anthropic.claude-sonnet-4-20250514", 100, 50)
        assert result.model_id == "anthropic.claude-sonnet-4-20250514"

    def test_preserves_token_counts(self, calculator: BedrockCostCalculator) -> None:
        """结果应保留 token 数量。"""
        result = calculator.calculate_cost("anthropic.claude-sonnet", 1234, 5678)
        assert result.tokens_input == 1234
        assert result.tokens_output == 5678
