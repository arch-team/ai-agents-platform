"""Budget 仓库接口。"""

from abc import abstractmethod

from src.modules.billing.domain.entities.budget import Budget
from src.shared.domain.repositories import IRepository


class IBudgetRepository(IRepository[Budget, int]):
    """Budget 仓库接口，扩展标准 CRUD 操作。"""

    @abstractmethod
    async def get_by_department_month(self, department_id: int, year: int, month: int) -> Budget | None:
        """根据部门和年月获取预算。"""

    @abstractmethod
    async def list_by_department(
        self, department_id: int, *, offset: int = 0, limit: int = 20,
    ) -> tuple[list[Budget], int]:
        """查询部门的所有预算记录，返回 (items, total)。"""
