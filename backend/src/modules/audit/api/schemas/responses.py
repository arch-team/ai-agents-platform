"""审计日志 API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """审计日志详情响应。"""

    id: int
    actor_id: int
    actor_name: str
    action: str
    category: str
    resource_type: str
    resource_id: str
    resource_name: str | None
    module: str
    ip_address: str | None
    user_agent: str | None
    request_method: str | None
    request_path: str | None
    status_code: int | None
    result: str
    error_message: str | None
    details: dict[str, str | int | float | bool | None] | None
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime


class AuditLogListResponse(BaseModel):
    """审计日志列表响应。"""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditStatsResponse(BaseModel):
    """审计统计响应。"""

    by_category: dict[str, int]
    by_action: dict[str, int]
    total: int
