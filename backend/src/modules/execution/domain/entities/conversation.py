"""对话会话实体。"""

from pydantic import Field

from src.modules.execution.domain.value_objects.conversation_status import (
    ConversationStatus,
)
from src.shared.domain.base_entity import PydanticEntity


class Conversation(PydanticEntity):
    """对话会话实体。"""

    title: str = Field(max_length=200, default="")
    agent_id: int
    user_id: int
    status: ConversationStatus = ConversationStatus.ACTIVE
    message_count: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    department_id: int | None = None  # 所属部门 (允许 NULL, 渐进填充)

    def _require_active(self, target: str) -> None:
        self._require_status(self.status, ConversationStatus.ACTIVE, target)

    def complete(self) -> None:
        """结束对话。ACTIVE -> COMPLETED。"""
        self._require_active(ConversationStatus.COMPLETED.value)
        self.status = ConversationStatus.COMPLETED
        self.touch()

    def fail(self) -> None:
        """标记对话为失败。ACTIVE -> FAILED。"""
        self._require_active(ConversationStatus.FAILED.value)
        self.status = ConversationStatus.FAILED
        self.touch()

    def add_message_count(self, token_count: int = 0) -> None:
        """增加消息计数和 Token 统计。仅 ACTIVE 状态可操作。"""
        self._require_active("add_message")
        self.message_count += 1
        self.total_tokens += token_count
        self.touch()
