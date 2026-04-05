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


# ── Blueprint 详情响应 ──


class BlueprintToolBindingResponse(BaseModel):
    """Blueprint 工具绑定。"""

    tool_id: int
    display_name: str
    usage_hint: str


class BlueprintPersonaResponse(BaseModel):
    """Blueprint 角色定义。"""

    role: str = ""
    background: str = ""
    tone: str = ""


class BlueprintGuardrailResponse(BaseModel):
    """Blueprint 安全护栏。"""

    rule: str
    severity: str = "warn"


class BlueprintDetailResponse(BaseModel):
    """Blueprint 完整配置响应。"""

    persona: BlueprintPersonaResponse
    guardrails: list[BlueprintGuardrailResponse] = Field(default_factory=list)
    memory_config: dict[str, object] = Field(default_factory=dict)
    knowledge_base_ids: list[int] = Field(default_factory=list)
    skill_ids: list[int] = Field(default_factory=list)
    tool_bindings: list[BlueprintToolBindingResponse] = Field(default_factory=list)
