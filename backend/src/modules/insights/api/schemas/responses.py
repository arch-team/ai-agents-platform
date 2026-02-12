"""Insights API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class UsageRecordResponse(BaseModel):
    """使用记录响应。"""

    id: int
    user_id: int
    agent_id: int
    conversation_id: int | None
    model_id: str
    tokens_input: int
    tokens_output: int
    estimated_cost: float
    recorded_at: datetime
    created_at: datetime


class UsageRecordListResponse(BaseModel):
    """使用记录列表响应。"""

    items: list[UsageRecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UsageSummaryResponse(BaseModel):
    """使用量摘要响应。"""

    total_tokens: int
    total_cost: float
    conversation_count: int
    record_count: int
    period: str
