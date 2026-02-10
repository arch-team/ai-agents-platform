"""Agent 相关 DTO。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateAgentDTO:
    """创建 Agent 请求数据。"""

    name: str
    description: str = ""
    system_prompt: str = ""
    model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    temperature: float = 0.7
    max_tokens: int = 2048
    runtime_type: str = "agent"


@dataclass
class UpdateAgentDTO:
    """更新 Agent 请求数据。"""

    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    model_id: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    runtime_type: str | None = None


@dataclass
class AgentDTO:
    """Agent 响应数据。"""

    id: int
    name: str
    description: str
    system_prompt: str
    status: str
    owner_id: int
    model_id: str
    temperature: float
    max_tokens: int
    top_p: float
    runtime_type: str
    created_at: datetime
    updated_at: datetime


@dataclass
class PagedAgentDTO:
    """Agent 分页响应数据。"""

    items: list[AgentDTO]
    total: int
    page: int
    page_size: int
