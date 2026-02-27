"""Billing API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.dependencies import get_current_user, require_role
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.billing.api.dependencies import get_billing_service
from src.modules.billing.api.schemas.requests import (
    CreateBudgetRequest,
    CreateDepartmentRequest,
    UpdateBudgetRequest,
    UpdateDepartmentRequest,
)
from src.modules.billing.api.schemas.responses import (
    BudgetListResponse,
    BudgetResponse,
    DepartmentCostPointResponse,
    DepartmentCostReportResponse,
    DepartmentListResponse,
    DepartmentResponse,
)
from src.modules.billing.application.dto.budget_dto import BudgetDTO, CreateBudgetDTO, UpdateBudgetDTO
from src.modules.billing.application.dto.department_dto import CreateDepartmentDTO, DepartmentDTO, UpdateDepartmentDTO
from src.modules.billing.application.services.billing_service import BillingService
from src.shared.api.schemas import calc_total_pages
from src.shared.domain.value_objects.role import Role


router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

ServiceDep = Annotated[BillingService, Depends(get_billing_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


def _to_department_response(dto: DepartmentDTO) -> DepartmentResponse:
    """DepartmentDTO -> DepartmentResponse。"""
    return DepartmentResponse(
        id=dto.id,
        name=dto.name,
        code=dto.code,
        description=dto.description,
        is_active=dto.is_active,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


def _to_budget_response(dto: BudgetDTO) -> BudgetResponse:
    """BudgetDTO -> BudgetResponse。"""
    return BudgetResponse(
        id=dto.id,
        department_id=dto.department_id,
        year=dto.year,
        month=dto.month,
        budget_amount=dto.budget_amount,
        used_amount=dto.used_amount,
        alert_threshold=dto.alert_threshold,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


# ── Department 端点 ──


@router.post("/departments", status_code=status.HTTP_201_CREATED)
async def create_department(
    request: CreateDepartmentRequest,
    service: ServiceDep,
    current_user: Annotated[UserDTO, Depends(require_role(Role.ADMIN))],
) -> DepartmentResponse:
    """创建部门。仅 ADMIN 可创建。"""
    dto = CreateDepartmentDTO(
        name=request.name,
        code=request.code,
        description=request.description,
    )
    dept = await service.create_department(dto, current_user.role)
    return _to_department_response(dept)


@router.get("/departments")
async def list_departments(
    service: ServiceDep,
    _current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DepartmentListResponse:
    """获取部门列表。"""
    paged = await service.list_departments(page=page, page_size=page_size)
    return DepartmentListResponse(
        items=[_to_department_response(d) for d in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/departments/{department_id}")
async def get_department(department_id: int, service: ServiceDep, _current_user: CurrentUserDep) -> DepartmentResponse:
    """获取部门详情。"""
    dept = await service.get_department(department_id)
    return _to_department_response(dept)


@router.put("/departments/{department_id}")
async def update_department(
    department_id: int,
    request: UpdateDepartmentRequest,
    service: ServiceDep,
    current_user: Annotated[UserDTO, Depends(require_role(Role.ADMIN))],
) -> DepartmentResponse:
    """更新部门。仅 ADMIN 可更新。"""
    dto = UpdateDepartmentDTO(
        name=request.name,
        description=request.description,
        is_active=request.is_active,
    )
    dept = await service.update_department(department_id, dto, current_user.role)
    return _to_department_response(dept)


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int,
    service: ServiceDep,
    current_user: Annotated[UserDTO, Depends(require_role(Role.ADMIN))],
) -> None:
    """删除部门。仅 ADMIN 可删除。"""
    await service.delete_department(department_id, current_user.role)


# ── Budget 端点 ──


@router.post("/budgets", status_code=status.HTTP_201_CREATED)
async def create_budget(
    request: CreateBudgetRequest,
    service: ServiceDep,
    current_user: Annotated[UserDTO, Depends(require_role(Role.ADMIN))],
) -> BudgetResponse:
    """创建预算。仅 ADMIN 可创建。"""
    dto = CreateBudgetDTO(
        department_id=request.department_id,
        year=request.year,
        month=request.month,
        budget_amount=request.budget_amount,
        alert_threshold=request.alert_threshold,
    )
    budget = await service.create_budget(dto, current_user.role)
    return _to_budget_response(budget)


@router.get("/budgets")
async def list_budgets(
    service: ServiceDep,
    _current_user: CurrentUserDep,
    department_id: Annotated[int, Query(gt=0)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> BudgetListResponse:
    """查询部门预算列表。"""
    paged = await service.list_budgets_by_department(department_id, page=page, page_size=page_size)
    return BudgetListResponse(
        items=[_to_budget_response(b) for b in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/departments/{department_id}/budgets/current")
async def get_current_budget(
    department_id: int,
    service: ServiceDep,
    _current_user: CurrentUserDep,
    year: Annotated[int, Query(ge=2020, le=2100)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> BudgetResponse:
    """获取部门当前月预算。"""
    budget = await service.get_current_budget(department_id, year, month)
    return _to_budget_response(budget)


@router.put("/budgets/{budget_id}")
async def update_budget(
    budget_id: int,
    request: UpdateBudgetRequest,
    service: ServiceDep,
    current_user: Annotated[UserDTO, Depends(require_role(Role.ADMIN))],
) -> BudgetResponse:
    """更新预算。仅 ADMIN 可更新。"""
    dto = UpdateBudgetDTO(
        budget_amount=request.budget_amount,
        alert_threshold=request.alert_threshold,
    )
    budget = await service.update_budget(budget_id, dto, current_user.role)
    return _to_budget_response(budget)


# ── Department Cost Report 端点 ──


@router.get("/departments/{department_id}/cost-report")
async def get_department_cost_report(
    department_id: int,
    service: ServiceDep,
    _current_user: CurrentUserDep,
    start_date: Annotated[str, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")],
    end_date: Annotated[str, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")],
) -> DepartmentCostReportResponse:
    """获取部门成本报告。"""
    report = await service.get_department_cost_report(department_id, start_date, end_date)
    return DepartmentCostReportResponse(
        department_id=report.department_id,
        department_code=report.department_code,
        department_name=report.department_name,
        total_cost=report.total_cost,
        budget_amount=report.budget_amount,
        used_percentage=report.used_percentage,
        daily_costs=[
            DepartmentCostPointResponse(
                date=point.date,
                department_code=point.department_code,
                amount=point.amount,
                currency=point.currency,
            )
            for point in report.daily_costs
        ],
        start_date=report.start_date,
        end_date=report.end_date,
        currency=report.currency,
    )
