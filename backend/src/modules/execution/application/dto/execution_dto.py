"""Execution 模块 DTO。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateConversationDTO:
    """创建对话请求数据。"""

    agent_id: int
    title: str = ""


@dataclass
class SendMessageDTO:
    """发送消息请求数据。"""

    content: str


@dataclass
class MessageDTO:
    """消息响应数据。"""

    id: int
    conversation_id: int
    role: str
    content: str
    token_count: int
    created_at: datetime


@dataclass
class ConversationDTO:
    """对话响应数据。"""

    id: int
    title: str
    agent_id: int
    user_id: int
    status: str
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime


@dataclass
class ConversationDetailDTO:
    """对话详情响应数据（含消息历史）。"""

    conversation: ConversationDTO
    messages: list[MessageDTO]


@dataclass
class PagedConversationDTO:
    """对话分页响应数据。"""

    items: list[ConversationDTO]
    total: int
    page: int
    page_size: int
