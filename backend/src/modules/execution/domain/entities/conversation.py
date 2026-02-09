"""对话会话实体。"""

from pydantic import ConfigDict, Field

from src.modules.execution.domain.value_objects.conversation_status import (
    ConversationStatus,
)
from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import InvalidStateTransitionError


class Conversation(PydanticEntity):
    """对话会话实体。"""

    title: str = Field(max_length=200, default="")
    agent_id: int
    user_id: int
    status: ConversationStatus = ConversationStatus.ACTIVE
    message_count: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)

    model_config = ConfigDict(validate_assignment=True)

    def complete(self) -> None:
        """结束对话。ACTIVE -> COMPLETED。"""
        if self.status != ConversationStatus.ACTIVE:
            raise InvalidStateTransitionError(
                entity_type="Conversation",
                current_state=self.status.value,
                target_state=ConversationStatus.COMPLETED.value,
            )
        self.status = ConversationStatus.COMPLETED
        self.touch()

    def fail(self) -> None:
        """标记对话为失败。ACTIVE -> FAILED。"""
        if self.status != ConversationStatus.ACTIVE:
            raise InvalidStateTransitionError(
                entity_type="Conversation",
                current_state=self.status.value,
                target_state=ConversationStatus.FAILED.value,
            )
        self.status = ConversationStatus.FAILED
        self.touch()

    def add_message_count(self, token_count: int = 0) -> None:
        """增加消息计数和 Token 统计。仅 ACTIVE 状态可操作。"""
        if self.status != ConversationStatus.ACTIVE:
            raise InvalidStateTransitionError(
                entity_type="Conversation",
                current_state=self.status.value,
                target_state="add_message",
            )
        self.message_count += 1
        self.total_tokens += token_count
        self.touch()
