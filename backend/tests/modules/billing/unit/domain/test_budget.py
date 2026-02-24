"""Budget 实体测试。"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.modules.billing.domain.entities.budget import Budget
from src.shared.domain.exceptions import ValidationError


class TestBudget:
    """Budget 实体测试。"""

    def test_create_budget_with_valid_data(self) -> None:
        """测试：使用有效数据创建预算。"""
        budget = Budget(
            department_id=1,
            year=2024,
            month=2,
            budget_amount=10000.0,
        )
        assert budget.department_id == 1
        assert budget.year == 2024
        assert budget.month == 2
        assert budget.budget_amount == 10000.0
        assert budget.used_amount == 0.0
        assert budget.alert_threshold == 0.8

    def test_create_budget_with_invalid_year_raises(self) -> None:
        """测试：无效年份抛出异常。"""
        with pytest.raises(PydanticValidationError):
            Budget(
                department_id=1,
                year=2019,  # < 2020
                month=2,
                budget_amount=10000.0,
            )

    def test_create_budget_with_invalid_month_raises(self) -> None:
        """测试：无效月份抛出异常。"""
        with pytest.raises(PydanticValidationError):
            Budget(
                department_id=1,
                year=2024,
                month=13,  # > 12
                budget_amount=10000.0,
            )

    def test_create_budget_with_negative_amount_raises(self) -> None:
        """测试：负数金额抛出异常。"""
        with pytest.raises(PydanticValidationError):
            Budget(
                department_id=1,
                year=2024,
                month=2,
                budget_amount=-100.0,  # 负数
            )

    def test_is_exceeded_returns_true_when_used_exceeds_budget(self) -> None:
        """测试：已使用金额超过预算时返回 True。"""
        budget = Budget(
            department_id=1,
            year=2024,
            month=2,
            budget_amount=10000.0,
            used_amount=10001.0,
        )
        assert budget.is_exceeded() is True

    def test_is_exceeded_returns_false_when_within_budget(self) -> None:
        """测试：未超预算时返回 False。"""
        budget = Budget(
            department_id=1,
            year=2024,
            month=2,
            budget_amount=10000.0,
            used_amount=5000.0,
        )
        assert budget.is_exceeded() is False

    def test_is_alert_threshold_reached_returns_true(self) -> None:
        """测试：达到告警阈值时返回 True。"""
        budget = Budget(
            department_id=1,
            year=2024,
            month=2,
            budget_amount=10000.0,
            used_amount=8000.0,  # 80%
            alert_threshold=0.8,
        )
        assert budget.is_alert_threshold_reached() is True

    def test_is_alert_threshold_reached_returns_false(self) -> None:
        """测试：未达到告警阈值时返回 False。"""
        budget = Budget(
            department_id=1,
            year=2024,
            month=2,
            budget_amount=10000.0,
            used_amount=7000.0,  # 70%
            alert_threshold=0.8,
        )
        assert budget.is_alert_threshold_reached() is False

    def test_add_usage_increases_used_amount(self) -> None:
        """测试：add_usage 增加已使用金额。"""
        budget = Budget(
            department_id=1,
            year=2024,
            month=2,
            budget_amount=10000.0,
            used_amount=1000.0,
        )
        budget.add_usage(500.0)
        assert budget.used_amount == 1500.0

    def test_add_usage_with_negative_amount_raises(self) -> None:
        """测试：add_usage 传入负数抛出异常。"""
        budget = Budget(
            department_id=1,
            year=2024,
            month=2,
            budget_amount=10000.0,
        )
        with pytest.raises(ValidationError, match="使用金额不能为负数"):
            budget.add_usage(-100.0)
