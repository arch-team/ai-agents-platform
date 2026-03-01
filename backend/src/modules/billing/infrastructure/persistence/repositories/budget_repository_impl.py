"""Budget 仓库实现。"""

from sqlalchemy import select

from src.modules.billing.domain.entities.budget import Budget
from src.modules.billing.domain.repositories.budget_repository import IBudgetRepository
from src.modules.billing.infrastructure.persistence.models.budget_model import BudgetModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class BudgetRepositoryImpl(PydanticRepository[Budget, BudgetModel, int], IBudgetRepository):
    """Budget 仓库的 SQLAlchemy 实现。"""

    entity_class = Budget
    model_class = BudgetModel
    _updatable_fields: frozenset[str] = frozenset({"budget_amount", "used_amount", "alert_threshold"})

    async def get_by_department_month(self, department_id: int, year: int, month: int) -> Budget | None:
        """根据部门和年月获取预算。"""
        stmt = select(BudgetModel).where(
            BudgetModel.department_id == department_id,
            BudgetModel.year == year,
            BudgetModel.month == month,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_department(
        self,
        department_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Budget], int]:
        """查询部门的所有预算记录，返回 (items, total)。"""
        return await self._list_and_count(
            BudgetModel.department_id == department_id,
            offset=offset,
            limit=limit,
        )
