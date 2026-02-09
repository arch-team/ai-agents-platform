"""Tool Catalog API 请求模型。"""

from pydantic import BaseModel, Field


class CreateToolRequest(BaseModel):
    """创建 Tool 请求。"""

    name: str = Field(min_length=1, max_length=100)
    tool_type: str = Field(...)  # "mcp_server" | "api" | "function"
    description: str = Field(max_length=1000, default="")
    version: str = Field(max_length=50, default="1.0.0")
    server_url: str = Field(max_length=500, default="")
    transport: str = Field(max_length=30, default="stdio")
    endpoint_url: str = Field(max_length=500, default="")
    method: str = Field(max_length=10, default="POST")
    runtime: str = Field(max_length=20, default="")
    handler: str = Field(max_length=200, default="")
    code_uri: str = Field(max_length=500, default="")
    auth_type: str = Field(max_length=20, default="none")


class UpdateToolRequest(BaseModel):
    """更新 Tool 请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    version: str | None = Field(default=None, max_length=50)
    server_url: str | None = Field(default=None, max_length=500)
    transport: str | None = Field(default=None, max_length=30)
    endpoint_url: str | None = Field(default=None, max_length=500)
    method: str | None = Field(default=None, max_length=10)
    runtime: str | None = Field(default=None, max_length=20)
    handler: str | None = Field(default=None, max_length=200)
    code_uri: str | None = Field(default=None, max_length=500)
    auth_type: str | None = Field(default=None, max_length=20)


class RejectToolRequest(BaseModel):
    """拒绝 Tool 请求。"""

    comment: str = Field(min_length=1, max_length=1000)
