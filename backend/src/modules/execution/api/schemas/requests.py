"""Execution API 请求模型。"""

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    """创建对话请求。"""

    agent_id: int
    title: str = Field(max_length=200, default="")


class SendMessageRequest(BaseModel):
    """发送消息请求。"""

    content: str = Field(min_length=1, max_length=100000)
