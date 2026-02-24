"""Department 仓库接口。"""

from abc import abstractmethod

from src.shared.domain.entities.department import Department
from src.shared.domain.repositories import IRepository


class IDepartmentRepository(IRepository[Department, int]):
    """Department 仓库接口，扩展标准 CRUD 操作。"""

    @abstractmethod
    async def get_by_code(self, code: str) -> Department | None:
        """根据部门编码获取部门。"""

    @abstractmethod
    async def list_all(self, *, offset: int = 0, limit: int = 20) -> tuple[list[Department], int]:
        """获取所有部门列表，返回 (items, total)。"""
