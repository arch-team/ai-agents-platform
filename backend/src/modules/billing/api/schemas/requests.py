"""Billing API 请求模型。"""

from pydantic import BaseModel, Field


class CreateDepartmentRequest(BaseModel):
    """创建部门请求。"""

    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=50)
    description: str = Field(max_length=500, default="")


class UpdateDepartmentRequest(BaseModel):
    """更新部门请求。"""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class CreateBudgetRequest(BaseModel):
    """创建预算请求。"""

    department_id: int = Field(gt=0)
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)
    budget_amount: float = Field(ge=0.0)
    alert_threshold: float = Field(ge=0.0, le=1.0, default=0.8)


class UpdateBudgetRequest(BaseModel):
    """更新预算请求。"""

    budget_amount: float | None = Field(None, ge=0.0)
    alert_threshold: float | None = Field(None, ge=0.0, le=1.0)
