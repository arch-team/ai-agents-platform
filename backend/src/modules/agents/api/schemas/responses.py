"""Agents API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class AgentConfigResponse(BaseModel):
    """Agent 配置响应。"""

    model_id: str
    temperature: float
    max_tokens: int
    top_p: float
    runtime_type: str
    enable_teams: bool
    enable_memory: bool
    tool_ids: list[int] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Agent 详情响应。"""

    id: int
    name: str
    description: str
    system_prompt: str
    status: str
    owner_id: int
    config: AgentConfigResponse
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    """Agent 列表响应。"""

    items: list[AgentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
