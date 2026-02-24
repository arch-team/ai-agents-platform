"""Budget 实体 — 部门月度预算管理。"""

from pydantic import Field, field_validator

from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import ValidationError


class Budget(PydanticEntity):
    """预算实体，管理部门的月度预算和使用情况。"""

    department_id: int
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)
    budget_amount: float = Field(ge=0.0)  # 月度预算金额 (USD)
    used_amount: float = Field(ge=0.0, default=0.0)  # 已使用金额
    alert_threshold: float = Field(ge=0.0, le=1.0, default=0.8)  # 告警阈值 (80%)

    @field_validator("budget_amount", "used_amount")
    @classmethod
    def validate_amounts(cls, value: float) -> float:
        """验证金额为非负数且最多两位小数。"""
        if value < 0:
            raise ValidationError(message="金额不能为负数", field="amount")
        # 验证最多两位小数
        if round(value, 2) != value:
            raise ValidationError(message="金额最多保留两位小数", field="amount")
        return value

    def is_exceeded(self) -> bool:
        """检查预算是否已超支。"""
        return self.used_amount > self.budget_amount

    def is_alert_threshold_reached(self) -> bool:
        """检查是否达到告警阈值。"""
        if self.budget_amount == 0:
            return False
        return self.used_amount >= self.budget_amount * self.alert_threshold

    def add_usage(self, amount: float) -> None:
        """增加已使用金额。"""
        if amount < 0:
            raise ValidationError(message="使用金额不能为负数", field="amount")
        self.used_amount += amount
        self.touch()
