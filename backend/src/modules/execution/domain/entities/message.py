"""对话消息实体。"""

from pydantic import Field

from src.modules.execution.domain.value_objects.message_role import MessageRole
from src.shared.domain.base_entity import PydanticEntity


class Message(PydanticEntity):
    """对话消息实体。"""

    conversation_id: int
    role: MessageRole
    content: str = Field(max_length=100000, default="")
    token_count: int = Field(default=0, ge=0)
