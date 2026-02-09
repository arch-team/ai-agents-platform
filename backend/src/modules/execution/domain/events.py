"""Execution 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class ConversationCreatedEvent(DomainEvent):
    """对话创建事件。"""

    conversation_id: int = 0
    agent_id: int = 0
    user_id: int = 0


@dataclass
class MessageSentEvent(DomainEvent):
    """用户消息发送事件。"""

    conversation_id: int = 0
    message_id: int = 0
    user_id: int = 0


@dataclass
class MessageReceivedEvent(DomainEvent):
    """助手消息接收事件。"""

    conversation_id: int = 0
    message_id: int = 0
    token_count: int = 0
    model_id: str = ""


@dataclass
class ConversationCompletedEvent(DomainEvent):
    """对话完成事件。"""

    conversation_id: int = 0
    user_id: int = 0
