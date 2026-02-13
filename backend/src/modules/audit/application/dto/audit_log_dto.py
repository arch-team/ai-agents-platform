"""审计日志相关 DTO。"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CreateAuditLogDTO:
    """创建审计日志请求数据。"""

    actor_id: int
    actor_name: str
    action: str
    category: str
    resource_type: str
    resource_id: str
    module: str
    resource_name: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_method: str | None = None
    request_path: str | None = None
    status_code: int | None = None
    result: str = "success"
    error_message: str | None = None
    details: dict[str, str | int | float | bool | None] | None = None
    occurred_at: datetime | None = None


@dataclass
class AuditLogDTO:
    """审计日志响应数据。"""

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


@dataclass
class AuditStatsDTO:
    """审计统计结果。"""

    by_category: dict[str, int] = field(default_factory=dict)
    by_action: dict[str, int] = field(default_factory=dict)
    total: int = 0
