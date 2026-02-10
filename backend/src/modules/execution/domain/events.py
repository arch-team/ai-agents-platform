"""Execution 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class _ExecutionEvent(DomainEvent):
    """Execution 事件基类，携带 conversation_id。"""

    conversation_id: int = 0


@dataclass
class ConversationCreatedEvent(_ExecutionEvent):
    """对话创建事件。"""

    agent_id: int = 0
    user_id: int = 0


@dataclass
class MessageSentEvent(_ExecutionEvent):
    """用户消息发送事件。"""

    message_id: int = 0
    user_id: int = 0


@dataclass
class MessageReceivedEvent(_ExecutionEvent):
    """助手消息接收事件。"""

    message_id: int = 0
    token_count: int = 0
    model_id: str = ""


@dataclass
class ConversationCompletedEvent(_ExecutionEvent):
    """对话完成事件。"""

    user_id: int = 0
