"""Billing API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel

from src.shared.api.schemas import PageResponse


class DepartmentResponse(BaseModel):
    """部门响应模型。"""

    id: int
    name: str
    code: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DepartmentListResponse(PageResponse[DepartmentResponse]):
    """部门列表响应。"""


class BudgetResponse(BaseModel):
    """预算响应模型。"""

    id: int
    department_id: int
    year: int
    month: int
    budget_amount: float
    used_amount: float
    alert_threshold: float
    created_at: datetime
    updated_at: datetime


class BudgetListResponse(PageResponse[BudgetResponse]):
    """预算列表响应。"""
