"""仓库泛型接口定义。"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.shared.domain.base_entity import PydanticEntity


E = TypeVar("E", bound=PydanticEntity)
ID = TypeVar("ID")


class IRepository(ABC, Generic[E, ID]):
    """仓库泛型接口，定义标准 CRUD 操作。"""

    @abstractmethod
    async def get_by_id(self, entity_id: ID) -> E | None:
        """根据 ID 获取实体。"""

    @abstractmethod
    async def list(self, *, offset: int = 0, limit: int = 20) -> list[E]:
        """获取实体列表。"""

    @abstractmethod
    async def count(self) -> int:
        """统计实体总数。"""

    @abstractmethod
    async def create(self, entity: E) -> E:
        """创建实体。"""

    @abstractmethod
    async def update(self, entity: E) -> E:
        """更新实体。"""

    @abstractmethod
    async def delete(self, entity_id: ID) -> None:
        """删除实体。"""
