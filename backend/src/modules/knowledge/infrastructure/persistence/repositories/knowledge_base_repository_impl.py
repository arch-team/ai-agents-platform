"""KnowledgeBase 仓库实现。"""

from sqlalchemy import select

from src.modules.knowledge.domain.entities.knowledge_base import KnowledgeBase
from src.modules.knowledge.domain.repositories.knowledge_base_repository import (
    IKnowledgeBaseRepository,
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
    _updatable_fields: frozenset[str] = frozenset(
        {
            "name",
            "description",
            "status",
            "agent_id",
            "bedrock_kb_id",
            "s3_prefix",
        },
    )

    async def get_by_name_and_owner(self, name: str, owner_id: int) -> KnowledgeBase | None:  # noqa: D102
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.name == name, KnowledgeBaseModel.owner_id == owner_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_owner(self, owner_id: int, *, offset: int = 0, limit: int = 20) -> list[KnowledgeBase]:  # noqa: D102
        stmt = (
            select(KnowledgeBaseModel)
            .where(KnowledgeBaseModel.owner_id == owner_id)
            .offset(offset)
            .limit(limit)
            .order_by(KnowledgeBaseModel.id.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_owner(self, owner_id: int) -> int:  # noqa: D102
        return await self._count_where(KnowledgeBaseModel.owner_id == owner_id)
