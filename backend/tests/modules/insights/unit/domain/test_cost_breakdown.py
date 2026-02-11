"""CostBreakdown 值对象单元测试。"""

import pytest

from src.modules.insights.domain.value_objects.cost_breakdown import CostBreakdown


@pytest.mark.unit
class TestCostBreakdown:
    """CostBreakdown 值对象测试。"""

    def test_create_with_valid_data(self) -> None:
        breakdown = CostBreakdown(
            tokens_input=1000,
            tokens_output=500,
            input_cost=0.003,
            output_cost=0.0075,
            total_cost=0.0105,
            model_id="anthropic.claude-sonnet-4-20250514",
        )
        assert breakdown.tokens_input == 1000
        assert breakdown.tokens_output == 500
        assert breakdown.input_cost == 0.003
        assert breakdown.output_cost == 0.0075
        assert breakdown.total_cost == 0.0105
        assert breakdown.model_id == "anthropic.claude-sonnet-4-20250514"

    def test_is_frozen(self) -> None:
        """值对象应为不可变。"""
        breakdown = CostBreakdown(
            tokens_input=1000,
            tokens_output=500,
            input_cost=0.003,
            output_cost=0.0075,
            total_cost=0.0105,
            model_id="anthropic.claude-sonnet-4-20250514",
        )
        with pytest.raises(AttributeError):
            breakdown.tokens_input = 2000  # type: ignore[misc]

    def test_equality_by_value(self) -> None:
        """相等性应基于值。"""
        b1 = CostBreakdown(
            tokens_input=1000,
            tokens_output=500,
            input_cost=0.003,
            output_cost=0.0075,
            total_cost=0.0105,
            model_id="model-a",
        )
        b2 = CostBreakdown(
            tokens_input=1000,
            tokens_output=500,
            input_cost=0.003,
            output_cost=0.0075,
            total_cost=0.0105,
            model_id="model-a",
        )
        assert b1 == b2

    def test_inequality_by_value(self) -> None:
        """不同值的对象应不相等。"""
        b1 = CostBreakdown(
            tokens_input=1000,
            tokens_output=500,
            input_cost=0.003,
            output_cost=0.0075,
            total_cost=0.0105,
            model_id="model-a",
        )
        b2 = CostBreakdown(
            tokens_input=2000,
            tokens_output=500,
            input_cost=0.006,
            output_cost=0.0075,
            total_cost=0.0135,
            model_id="model-a",
        )
        assert b1 != b2
