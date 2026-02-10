"""Tool 相关 DTO。"""

from dataclasses import dataclass
from datetime import datetime

from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType


@dataclass
class CreateToolDTO:
    """创建 Tool 请求数据。"""

    name: str
    tool_type: ToolType
    description: str = ""
    version: str = "1.0.0"
    server_url: str = ""
    transport: str = "stdio"
    endpoint_url: str = ""
    method: str = "POST"
    headers: list[tuple[str, str]] | None = None
    runtime: str = ""
    handler: str = ""
    code_uri: str = ""
    auth_type: str = "none"
    auth_config: list[tuple[str, str]] | None = None
    allowed_roles: list[str] | None = None


@dataclass
class UpdateToolDTO:
    """更新 Tool 请求数据。"""

    name: str | None = None
    description: str | None = None
    version: str | None = None
    server_url: str | None = None
    transport: str | None = None
    endpoint_url: str | None = None
    method: str | None = None
    headers: list[tuple[str, str]] | None = None
    runtime: str | None = None
    handler: str | None = None
    code_uri: str | None = None
    auth_type: str | None = None
    auth_config: list[tuple[str, str]] | None = None
    allowed_roles: list[str] | None = None


@dataclass
class ToolDTO:
    """Tool 响应数据。"""

    id: int
    name: str
    description: str
    tool_type: str
    version: str
    status: str
    creator_id: int
    server_url: str
    transport: str
    endpoint_url: str
    method: str
    headers: list[tuple[str, str]]
    runtime: str
    handler: str
    code_uri: str
    auth_type: str
    auth_config: list[tuple[str, str]]
    allowed_roles: list[str]
    reviewer_id: int | None
    review_comment: str
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass
class PagedToolDTO:
    """Tool 分页响应数据。"""

    items: list[ToolDTO]
    total: int
    page: int
    page_size: int
