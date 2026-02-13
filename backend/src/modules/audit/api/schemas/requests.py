"""审计日志 API 请求模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogQueryParams(BaseModel):
    """审计日志列表查询参数。"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    category: str | None = Field(default=None, max_length=50)
    action: str | None = Field(default=None, max_length=50)
    actor_id: int | None = None
    resource_type: str | None = Field(default=None, max_length=50)
    resource_id: str | None = Field(default=None, max_length=100)
    start_date: datetime | None = None
    end_date: datetime | None = None


class AuditLogResourceParams(BaseModel):
    """按资源查询审计日志参数。"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AuditLogStatsParams(BaseModel):
    """审计统计查询参数。"""

    start_date: datetime | None = None
    end_date: datetime | None = None


class AuditLogExportParams(BaseModel):
    """审计日志导出参数。"""

    category: str | None = Field(default=None, max_length=50)
    action: str | None = Field(default=None, max_length=50)
    actor_id: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    max_rows: int = Field(default=10000, ge=1, le=100000)
