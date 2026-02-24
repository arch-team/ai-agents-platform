"""Billing 领域异常。"""

from src.shared.domain.exceptions import DomainError


class DepartmentNotFoundError(DomainError):
    """部门不存在。"""

    def __init__(self, department_id: int | None = None, code: str | None = None) -> None:
        identifier = f"ID {department_id}" if department_id else f"编码 {code}"
        super().__init__(
            message=f"部门不存在: {identifier}",
            code="DEPARTMENT_NOT_FOUND",
        )


class BudgetNotFoundError(DomainError):
    """预算不存在。"""

    def __init__(self, budget_id: int | None = None, department_id: int | None = None) -> None:
        identifier = f"ID {budget_id}" if budget_id else f"部门 {department_id}"
        super().__init__(
            message=f"预算不存在: {identifier}",
            code="BUDGET_NOT_FOUND",
        )


class DuplicateDepartmentCodeError(DomainError):
    """部门编码重复。"""

    def __init__(self, code: str) -> None:
        super().__init__(
            message=f"部门编码已存在: {code}",
            code="DUPLICATE_DEPARTMENT_CODE",
        )


class BudgetExceededError(DomainError):
    """预算超支。"""

    def __init__(self, department_id: int, year: int, month: int) -> None:
        super().__init__(
            message=f"部门 {department_id} 在 {year}-{month:02d} 的预算已超支",
            code="BUDGET_EXCEEDED",
        )
