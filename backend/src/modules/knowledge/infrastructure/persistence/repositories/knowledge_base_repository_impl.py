"""KnowledgeBase 仓库实现。"""

from sqlalchemy import func, select

from src.modules.knowledge.domain.entities.knowledge_base import KnowledgeBase
from src.modules.knowledge.domain.repositories.knowledge_base_repository import (
    IKnowledgeBaseRepository,
)
from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)
from src.modules.knowledge.infrastructure.persistence.models.knowledge_base_model import (
    KnowledgeBaseModel,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class KnowledgeBaseRepositoryImpl(
    PydanticRepository[KnowledgeBase, KnowledgeBaseModel, int],
    IKnowledgeBaseRepository,
):
    """KnowledgeBase 仓库的 SQLAlchemy 实现。"""

    entity_class = KnowledgeBase
    model_class = KnowledgeBaseModel
    _updatable_fields: frozenset[str] = frozenset({
        "name", "description", "status", "agent_id",
        "bedrock_kb_id", "s3_prefix",
    })

    def _to_entity(self, model: KnowledgeBaseModel) -> KnowledgeBase:
        return KnowledgeBase(
            id=model.id,
            name=model.name,
            description=model.description,
            status=KnowledgeBaseStatus(model.status),
            owner_id=model.owner_id,
            agent_id=model.agent_id,
            bedrock_kb_id=model.bedrock_kb_id,
            s3_prefix=model.s3_prefix,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _from_entity(self, entity: KnowledgeBase) -> KnowledgeBaseModel:
        return KnowledgeBaseModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            status=entity.status.value,
            owner_id=entity.owner_id,
            agent_id=entity.agent_id,
            bedrock_kb_id=entity.bedrock_kb_id,
            s3_prefix=entity.s3_prefix,
        )

    async def get_by_name_and_owner(self, name: str, owner_id: int) -> KnowledgeBase | None:
        """按名称和所有者查询知识库。"""
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.name == name,
            KnowledgeBaseModel.owner_id == owner_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_owner(
        self, owner_id: int, *, offset: int = 0, limit: int = 20,
    ) -> list[KnowledgeBase]:
        """按所有者查询知识库列表。"""
        stmt = (
            select(KnowledgeBaseModel)
            .where(KnowledgeBaseModel.owner_id == owner_id)
            .offset(offset)
            .limit(limit)
            .order_by(KnowledgeBaseModel.id.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_owner(self, owner_id: int) -> int:
        """按所有者统计知识库数量。"""
        stmt = select(func.count()).select_from(KnowledgeBaseModel).where(
            KnowledgeBaseModel.owner_id == owner_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
