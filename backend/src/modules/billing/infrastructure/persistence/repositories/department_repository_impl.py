"""Department 仓库实现。"""

from sqlalchemy import select

from src.modules.billing.domain.repositories.department_repository import IDepartmentRepository
from src.shared.domain.entities.department import Department
from src.shared.infrastructure.persistence.department_model import DepartmentModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class DepartmentRepositoryImpl(PydanticRepository[Department, DepartmentModel, int], IDepartmentRepository):
    """Department 仓库的 SQLAlchemy 实现。"""

    entity_class = Department
    model_class = DepartmentModel
    _updatable_fields: frozenset[str] = frozenset({"name", "description", "is_active"})

    async def get_by_code(self, code: str) -> Department | None:
        """根据部门编码获取部门。"""
        stmt = select(DepartmentModel).where(DepartmentModel.code == code)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self, *, offset: int = 0, limit: int = 20) -> tuple[list[Department], int]:
        """获取所有部门列表，返回 (items, total)。"""
        return await self._list_and_count(offset=offset, limit=limit)
