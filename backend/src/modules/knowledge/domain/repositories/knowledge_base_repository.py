"""知识库仓库接口。"""

from abc import abstractmethod

from src.modules.knowledge.domain.entities.knowledge_base import KnowledgeBase
from src.shared.domain.repositories import IRepository


class IKnowledgeBaseRepository(IRepository[KnowledgeBase, int]):
    """知识库仓库接口。"""

    @abstractmethod
    async def get_by_name_and_owner(self, name: str, owner_id: int) -> KnowledgeBase | None:
        """按名称和所有者查询知识库。"""

    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[KnowledgeBase]:
        """按所有者查询知识库列表。"""

    @abstractmethod
    async def count_by_owner(self, owner_id: int) -> int:
        """按所有者统计知识库数量。"""
