"""Conversation 仓库实现。"""

from datetime import UTC, datetime

from sqlalchemy import ColumnElement, select, update

from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.repositories.conversation_repository import IConversationRepository
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

    async def increment_message_stats(
        self,
        conversation_id: int,
        *,
        message_delta: int = 0,
        token_delta: int = 0,
    ) -> None:
        """原子增量: UPDATE SET col = col + N, 锁持有时间极短。"""
        stmt = (
            update(ConversationModel)
            .where(ConversationModel.id == conversation_id)
            .values(
                message_count=ConversationModel.message_count + message_delta,
                total_tokens=ConversationModel.total_tokens + token_delta,
                updated_at=datetime.now(UTC),
            )
        )
        await self._session.execute(stmt)

    @staticmethod
    def _user_filters(user_id: int, agent_id: int | None = None) -> list[ColumnElement[bool]]:
        """构建 user 相关的查询条件。"""
        filters: list[ColumnElement[bool]] = [ConversationModel.user_id == user_id]
        if agent_id is not None:
            filters.append(ConversationModel.agent_id == agent_id)
        return filters

    async def list_by_user(
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Conversation]:
        filters = self._user_filters(user_id, agent_id)
        stmt = (
            select(ConversationModel).where(*filters).offset(offset).limit(limit).order_by(ConversationModel.id.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_user(
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
    ) -> int:
        return await self._count_where(*self._user_filters(user_id, agent_id))
