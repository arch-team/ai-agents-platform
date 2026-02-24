"""Billing 应用服务。"""

from src.modules.auth.domain.exceptions import AuthorizationError
from src.modules.auth.domain.value_objects.role import Role
from src.modules.billing.application.dto.budget_dto import BudgetDTO, CreateBudgetDTO, UpdateBudgetDTO
from src.modules.billing.application.dto.department_dto import CreateDepartmentDTO, DepartmentDTO, UpdateDepartmentDTO
from src.modules.billing.domain.entities.budget import Budget
from src.modules.billing.domain.events import BudgetCreatedEvent, BudgetExceededEvent, DepartmentCreatedEvent
from src.modules.billing.domain.exceptions import (
    BudgetExceededError,
    BudgetNotFoundError,
    DepartmentNotFoundError,
    DuplicateDepartmentCodeError,
)
from src.modules.billing.domain.repositories.budget_repository import IBudgetRepository
from src.modules.billing.domain.repositories.department_repository import IDepartmentRepository
from src.shared.application.dtos import PagedResult
from src.shared.domain.entities.department import Department
from src.shared.domain.event_bus import event_bus


def _to_department_dto(dept: Department) -> DepartmentDTO:
    """Department -> DepartmentDTO。"""
    assert dept.id is not None
    assert dept.created_at is not None
    assert dept.updated_at is not None
    return DepartmentDTO(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        is_active=dept.is_active,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


def _to_budget_dto(budget: Budget) -> BudgetDTO:
    """Budget -> BudgetDTO。"""
    assert budget.id is not None
    assert budget.created_at is not None
    assert budget.updated_at is not None
    return BudgetDTO(
        id=budget.id,
        department_id=budget.department_id,
        year=budget.year,
        month=budget.month,
        budget_amount=budget.budget_amount,
        used_amount=budget.used_amount,
        alert_threshold=budget.alert_threshold,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
    )


class BillingService:
    """Billing 业务服务，负责部门和预算管理。"""

    def __init__(self, department_repo: IDepartmentRepository, budget_repo: IBudgetRepository) -> None:
        self._department_repo = department_repo
        self._budget_repo = budget_repo

    def _require_admin(self, user_role: str) -> None:
        """要求 ADMIN 角色，否则抛出 AuthorizationError。"""
        if user_role != Role.ADMIN.value:
            raise AuthorizationError(message="仅管理员可执行此操作")

    # ── Department CRUD ──

    async def create_department(self, dto: CreateDepartmentDTO, user_role: str) -> DepartmentDTO:
        """创建部门。仅 ADMIN 可创建。

        Raises:
            DuplicateDepartmentCodeError: 部门编码已存在
            AuthorizationError: 权限不足
        """
        self._require_admin(user_role)

        existing = await self._department_repo.get_by_code(dto.code)
        if existing is not None:
            raise DuplicateDepartmentCodeError(dto.code)

        dept = Department(
            name=dto.name,
            code=dto.code,
            description=dto.description,
        )
        created = await self._department_repo.create(dept)

        await event_bus.publish_async(
            DepartmentCreatedEvent(
                department_id=created.id or 0,
                code=created.code,
                name=created.name,
            ),
        )

        return _to_department_dto(created)

    async def get_department(self, department_id: int) -> DepartmentDTO:
        """获取部门详情。

        Raises:
            DepartmentNotFoundError: 部门不存在
        """
        dept = await self._department_repo.get_by_id(department_id)
        if dept is None:
            raise DepartmentNotFoundError(department_id=department_id)
        return _to_department_dto(dept)

    async def list_departments(self, *, page: int = 1, page_size: int = 20) -> PagedResult[DepartmentDTO]:
        """列出所有部门。"""
        offset = (page - 1) * page_size
        items, total = await self._department_repo.list_all(offset=offset, limit=page_size)
        return PagedResult(
            items=[_to_department_dto(d) for d in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_department(self, department_id: int, dto: UpdateDepartmentDTO, user_role: str) -> DepartmentDTO:
        """更新部门。仅 ADMIN 可更新。

        Raises:
            DepartmentNotFoundError: 部门不存在
            AuthorizationError: 权限不足
        """
        self._require_admin(user_role)

        dept = await self._department_repo.get_by_id(department_id)
        if dept is None:
            raise DepartmentNotFoundError(department_id=department_id)

        if dto.name is not None:
            dept.name = dto.name
        if dto.description is not None:
            dept.description = dto.description
        if dto.is_active is not None:
            dept.is_active = dto.is_active

        dept.touch()
        updated = await self._department_repo.update(dept)
        return _to_department_dto(updated)

    async def delete_department(self, department_id: int, user_role: str) -> None:
        """删除部门。仅 ADMIN 可删除。

        Raises:
            DepartmentNotFoundError: 部门不存在
            AuthorizationError: 权限不足
        """
        self._require_admin(user_role)

        dept = await self._department_repo.get_by_id(department_id)
        if dept is None:
            raise DepartmentNotFoundError(department_id=department_id)

        await self._department_repo.delete(department_id)

    # ── Budget CRUD ──

    async def create_budget(self, dto: CreateBudgetDTO, user_role: str) -> BudgetDTO:
        """创建预算。仅 ADMIN 可创建。

        Raises:
            DepartmentNotFoundError: 部门不存在
            AuthorizationError: 权限不足
        """
        self._require_admin(user_role)

        # 验证部门存在
        dept = await self._department_repo.get_by_id(dto.department_id)
        if dept is None:
            raise DepartmentNotFoundError(department_id=dto.department_id)

        budget = Budget(
            department_id=dto.department_id,
            year=dto.year,
            month=dto.month,
            budget_amount=dto.budget_amount,
            alert_threshold=dto.alert_threshold,
        )
        created = await self._budget_repo.create(budget)

        await event_bus.publish_async(
            BudgetCreatedEvent(
                budget_id=created.id or 0,
                department_id=created.department_id,
                year=created.year,
                month=created.month,
                budget_amount=created.budget_amount,
            ),
        )

        return _to_budget_dto(created)

    async def get_budget(self, budget_id: int) -> BudgetDTO:
        """获取预算详情。

        Raises:
            BudgetNotFoundError: 预算不存在
        """
        budget = await self._budget_repo.get_by_id(budget_id)
        if budget is None:
            raise BudgetNotFoundError(budget_id=budget_id)
        return _to_budget_dto(budget)

    async def get_current_budget(self, department_id: int, year: int, month: int) -> BudgetDTO:
        """获取部门当前月预算。

        Raises:
            BudgetNotFoundError: 预算不存在
        """
        budget = await self._budget_repo.get_by_department_month(department_id, year, month)
        if budget is None:
            raise BudgetNotFoundError(department_id=department_id)
        return _to_budget_dto(budget)

    async def list_budgets_by_department(
        self,
        department_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[BudgetDTO]:
        """列出部门的所有预算记录。"""
        offset = (page - 1) * page_size
        items, total = await self._budget_repo.list_by_department(department_id, offset=offset, limit=page_size)
        return PagedResult(
            items=[_to_budget_dto(b) for b in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_budget(self, budget_id: int, dto: UpdateBudgetDTO, user_role: str) -> BudgetDTO:
        """更新预算。仅 ADMIN 可更新。

        Raises:
            BudgetNotFoundError: 预算不存在
            AuthorizationError: 权限不足
        """
        self._require_admin(user_role)

        budget = await self._budget_repo.get_by_id(budget_id)
        if budget is None:
            raise BudgetNotFoundError(budget_id=budget_id)

        if dto.budget_amount is not None:
            budget.budget_amount = dto.budget_amount
        if dto.alert_threshold is not None:
            budget.alert_threshold = dto.alert_threshold

        budget.touch()
        updated = await self._budget_repo.update(budget)

        # 检查更新后是否超支, 发布事件
        if updated.is_exceeded():
            await event_bus.publish_async(
                BudgetExceededEvent(
                    budget_id=updated.id or 0,
                    department_id=updated.department_id,
                    year=updated.year,
                    month=updated.month,
                    budget_amount=updated.budget_amount,
                    used_amount=updated.used_amount,
                ),
            )

        return _to_budget_dto(updated)

    async def add_budget_usage(self, department_id: int, year: int, month: int, amount: float) -> None:
        """增加预算使用金额（内部使用，供其他模块调用）。

        Raises:
            BudgetNotFoundError: 预算不存在
            BudgetExceededError: 预算超支
        """
        budget = await self._budget_repo.get_by_department_month(department_id, year, month)
        if budget is None:
            raise BudgetNotFoundError(department_id=department_id)

        budget.add_usage(amount)
        updated = await self._budget_repo.update(budget)

        # 超支时发布事件
        if updated.is_exceeded():
            await event_bus.publish_async(
                BudgetExceededEvent(
                    budget_id=updated.id or 0,
                    department_id=updated.department_id,
                    year=updated.year,
                    month=updated.month,
                    budget_amount=updated.budget_amount,
                    used_amount=updated.used_amount,
                ),
            )
            raise BudgetExceededError(department_id, year, month)
