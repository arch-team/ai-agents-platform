"""团队执行 API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class TeamExecutionResponse(BaseModel):
    """团队执行响应。"""

    id: int
    agent_id: int
    user_id: int
    conversation_id: int | None
    prompt: str
    status: str
    result: str
    error_message: str
    input_tokens: int
    output_tokens: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TeamExecutionListResponse(BaseModel):
    """团队执行列表响应。"""

    items: list[TeamExecutionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TeamExecutionLogResponse(BaseModel):
    """团队执行日志响应。"""

    id: int
    execution_id: int
    sequence: int
    log_type: str
    content: str
    created_at: datetime
