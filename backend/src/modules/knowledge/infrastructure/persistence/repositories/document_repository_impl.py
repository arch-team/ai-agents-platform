"""Document 仓库实现。"""

from sqlalchemy import func, select

from src.modules.knowledge.domain.entities.document import Document
from src.modules.knowledge.domain.repositories.document_repository import (
    IDocumentRepository,
)
from src.modules.knowledge.domain.value_objects.document_status import DocumentStatus
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
    _updatable_fields: frozenset[str] = frozenset({
        "filename", "s3_key", "file_size", "status",
        "content_type", "chunk_count",
    })

    def _to_entity(self, model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            knowledge_base_id=model.knowledge_base_id,
            filename=model.filename,
            s3_key=model.s3_key,
            file_size=model.file_size,
            status=DocumentStatus(model.status),
            content_type=model.content_type,
            chunk_count=model.chunk_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _from_entity(self, entity: Document) -> DocumentModel:
        return DocumentModel(
            id=entity.id,
            knowledge_base_id=entity.knowledge_base_id,
            filename=entity.filename,
            s3_key=entity.s3_key,
            file_size=entity.file_size,
            status=entity.status.value,
            content_type=entity.content_type,
            chunk_count=entity.chunk_count,
        )

    async def list_by_knowledge_base(
        self, knowledge_base_id: int, *, offset: int = 0, limit: int = 20,
    ) -> list[Document]:
        """按知识库查询文档列表。"""
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.knowledge_base_id == knowledge_base_id)
            .offset(offset)
            .limit(limit)
            .order_by(DocumentModel.id.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_knowledge_base(self, knowledge_base_id: int) -> int:
        """按知识库统计文档数量。"""
        stmt = select(func.count()).select_from(DocumentModel).where(
            DocumentModel.knowledge_base_id == knowledge_base_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
