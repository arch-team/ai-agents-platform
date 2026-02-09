"""Message 仓库实现。"""

from sqlalchemy import func, select

from src.modules.execution.domain.entities.message import Message
from src.modules.execution.domain.repositories.message_repository import IMessageRepository
from src.modules.execution.domain.value_objects.message_role import MessageRole
from src.modules.execution.infrastructure.persistence.models.message_model import MessageModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class MessageRepositoryImpl(
    PydanticRepository[Message, MessageModel, int],
    IMessageRepository,
):
    """Message 仓库的 SQLAlchemy 实现。"""

    entity_class = Message
    model_class = MessageModel
    _updatable_fields: frozenset[str] = frozenset({"content", "token_count"})

    def _to_entity(self, model: MessageModel) -> Message:
        return Message(
            id=model.id,
            conversation_id=model.conversation_id,
            role=MessageRole(model.role),
            content=model.content,
            token_count=model.token_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Message) -> MessageModel:
        return MessageModel(
            id=entity.id,
            conversation_id=entity.conversation_id,
            role=entity.role.value,
            content=entity.content,
            token_count=entity.token_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _get_update_data(self, entity: Message) -> dict[str, object]:
        return {
            "content": entity.content,
            "token_count": entity.token_count,
        }

    async def list_by_conversation(  # noqa: D102
        self,
        conversation_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Message]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .offset(offset)
            .limit(limit)
            .order_by(MessageModel.id.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_conversation(self, conversation_id: int) -> int:  # noqa: D102
        stmt = select(func.count()).select_from(MessageModel).where(MessageModel.conversation_id == conversation_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()
