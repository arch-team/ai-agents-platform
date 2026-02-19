"""IKnowledgeQuerier 的 knowledge 模块实现。"""

from src.modules.knowledge.application.interfaces.knowledge_service import (
    IKnowledgeService,
)
from src.modules.knowledge.domain.repositories.knowledge_base_repository import (
    IKnowledgeBaseRepository,
)
from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)
from src.shared.domain.interfaces.knowledge_querier import (
    IKnowledgeQuerier,
    RetrievalResult,
)


class KnowledgeQuerierImpl(IKnowledgeQuerier):
    """基于 knowledge 模块的 IKnowledgeQuerier 实现。

    通过内部 KB ID 查找 bedrock_kb_id，再调用 IKnowledgeService 执行检索。
    """

    def __init__(
        self,
        kb_repository: IKnowledgeBaseRepository,
        knowledge_service: IKnowledgeService,
    ) -> None:
        self._kb_repository = kb_repository
        self._knowledge_service = knowledge_service

    async def retrieve(
        self,
        kb_id: int,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """通过内部 ID 检索知识库。

        知识库不存在或非 ACTIVE 状态时返回空列表。
        """
        kb = await self._kb_repository.get_by_id(kb_id)
        if kb is None or kb.status != KnowledgeBaseStatus.ACTIVE or not kb.bedrock_kb_id:
            return []

        chunks = await self._knowledge_service.retrieve(
            kb.bedrock_kb_id,
            query,
            top_k=top_k,
        )
        return [RetrievalResult(content=chunk.content, score=chunk.score) for chunk in chunks]
