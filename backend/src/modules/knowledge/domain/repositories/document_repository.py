"""文档仓库接口。"""

from abc import abstractmethod

from src.modules.knowledge.domain.entities.document import Document
from src.shared.domain.repositories import IRepository


class IDocumentRepository(IRepository[Document, int]):
    """文档仓库接口。"""

    @abstractmethod
    async def list_by_knowledge_base(
        self,
        knowledge_base_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Document]:
        """按知识库查询文档列表。"""

    @abstractmethod
    async def count_by_knowledge_base(self, knowledge_base_id: int) -> int:
        """按知识库统计文档数量。"""
