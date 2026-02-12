"""Tool Catalog API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class ToolConfigResponse(BaseModel):
    """Tool 配置响应。"""

    server_url: str
    transport: str
    endpoint_url: str
    method: str
    runtime: str
    handler: str
    code_uri: str
    auth_type: str


class ToolResponse(BaseModel):
    """Tool 详情响应。"""

    id: int
    name: str
    description: str
    tool_type: str
    version: str
    status: str
    creator_id: int
    config: ToolConfigResponse
    allowed_roles: list[str]
    gateway_target_id: str
    reviewer_id: int | None
    review_comment: str
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ToolListResponse(BaseModel):
    """Tool 列表响应。"""

    items: list[ToolResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
