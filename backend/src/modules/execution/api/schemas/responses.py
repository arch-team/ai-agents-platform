"""Execution API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """消息响应。"""

    id: int
    conversation_id: int
    role: str
    content: str
    token_count: int
    created_at: datetime


class ConversationResponse(BaseModel):
    """对话响应。"""

    id: int
    title: str
    agent_id: int
    user_id: int
    status: str
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(BaseModel):
    """对话详情响应（含消息历史）。"""

    conversation: ConversationResponse
    messages: list[MessageResponse]


class ConversationListResponse(BaseModel):
    """对话列表响应。"""

    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
