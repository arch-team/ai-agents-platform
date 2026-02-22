"""Builder API 请求模型。"""

from pydantic import BaseModel, Field


class TriggerBuilderRequest(BaseModel):
    """创建 Builder 会话请求。"""

    prompt: str = Field(min_length=1, max_length=2000, description="用户对 Agent 的描述")


class ConfirmBuilderRequest(BaseModel):
    """确认创建 Agent 请求（预留扩展字段）。"""
