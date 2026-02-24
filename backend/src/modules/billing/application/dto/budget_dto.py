"""Budget DTO 定义。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateBudgetDTO:
    """创建预算 DTO。"""

    department_id: int
    year: int
    month: int
    budget_amount: float
    alert_threshold: float = 0.8


@dataclass
class UpdateBudgetDTO:
    """更新预算 DTO。"""

    budget_amount: float | None = None
    alert_threshold: float | None = None


@dataclass
class BudgetDTO:
    """预算 DTO (响应)。"""

    id: int
    department_id: int
    year: int
    month: int
    budget_amount: float
    used_amount: float
    alert_threshold: float
    created_at: datetime
    updated_at: datetime
