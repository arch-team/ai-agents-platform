"""Document 仓库实现。"""

from sqlalchemy import select

from src.modules.knowledge.domain.entities.document import Document
from src.modules.knowledge.domain.repositories.document_repository import (
    IDocumentRepository,
)
from src.modules.knowledge.infrastructure.persistence.models.document_model import (
    DocumentModel,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class DocumentRepositoryImpl(
    PydanticRepository[Document, DocumentModel, int],
    IDocumentRepository,
):
    """Document 仓库的 SQLAlchemy 实现。"""

    entity_class = Document
    model_class = DocumentModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "filename",
            "s3_key",
            "file_size",
            "status",
            "content_type",
            "chunk_count",
        },
    )

    async def list_by_knowledge_base(  # noqa: D102
        self,
        knowledge_base_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Document]:
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.knowledge_base_id == knowledge_base_id)
            .offset(offset)
            .limit(limit)
            .order_by(DocumentModel.id.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_knowledge_base(self, knowledge_base_id: int) -> int:  # noqa: D102
        return await self._count_where(DocumentModel.knowledge_base_id == knowledge_base_id)
