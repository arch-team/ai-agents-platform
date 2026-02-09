"""Conversation 仓库实现。"""

from sqlalchemy import func, select

from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.repositories.conversation_repository import IConversationRepository
from src.modules.execution.domain.value_objects.conversation_status import ConversationStatus
from src.modules.execution.infrastructure.persistence.models.conversation_model import (
    ConversationModel,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class ConversationRepositoryImpl(
    PydanticRepository[Conversation, ConversationModel, int],
    IConversationRepository,
):
    """Conversation 仓库的 SQLAlchemy 实现。"""

    entity_class = Conversation
    model_class = ConversationModel
    _updatable_fields: frozenset[str] = frozenset(
        {"title", "status", "message_count", "total_tokens"},
    )

    def _to_entity(self, model: ConversationModel) -> Conversation:
        return Conversation(
            id=model.id,
            title=model.title,
            agent_id=model.agent_id,
            user_id=model.user_id,
            status=ConversationStatus(model.status),
            message_count=model.message_count,
            total_tokens=model.total_tokens,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Conversation) -> ConversationModel:
        return ConversationModel(
            id=entity.id,
            title=entity.title,
            agent_id=entity.agent_id,
            user_id=entity.user_id,
            status=entity.status.value,
            message_count=entity.message_count,
            total_tokens=entity.total_tokens,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _get_update_data(self, entity: Conversation) -> dict[str, object]:
        return {
            "title": entity.title,
            "status": entity.status.value,
            "message_count": entity.message_count,
            "total_tokens": entity.total_tokens,
        }

    async def list_by_user(  # noqa: D102
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Conversation]:
        stmt = select(ConversationModel).where(ConversationModel.user_id == user_id)
        if agent_id is not None:
            stmt = stmt.where(ConversationModel.agent_id == agent_id)
        stmt = stmt.offset(offset).limit(limit).order_by(ConversationModel.id.desc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_user(  # noqa: D102
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(ConversationModel).where(ConversationModel.user_id == user_id)
        if agent_id is not None:
            stmt = stmt.where(ConversationModel.agent_id == agent_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()
