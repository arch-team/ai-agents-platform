"""Agents API 请求模型。"""

from pydantic import BaseModel, Field

from src.shared.domain.constants import (
    AGENT_DEFAULT_ENABLE_TEAMS,
    AGENT_DEFAULT_MAX_TOKENS,
    AGENT_DEFAULT_MODEL_ID,
    AGENT_DEFAULT_RUNTIME_TYPE,
    AGENT_DEFAULT_TEMPERATURE,
)


class CreateAgentRequest(BaseModel):
    """创建 Agent 请求。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    system_prompt: str = Field(max_length=10000, default="")
    model_id: str = Field(default=AGENT_DEFAULT_MODEL_ID, max_length=200)
    temperature: float = Field(default=AGENT_DEFAULT_TEMPERATURE, ge=0.0, le=1.0)
    max_tokens: int = Field(default=AGENT_DEFAULT_MAX_TOKENS, ge=1, le=4096)
    runtime_type: str = Field(default=AGENT_DEFAULT_RUNTIME_TYPE, pattern=r"^(agent|basic)$")
    enable_teams: bool = Field(default=AGENT_DEFAULT_ENABLE_TEAMS)
    enable_memory: bool = Field(default=False)
    tool_ids: list[int] = Field(default_factory=list, max_length=50)


class UpdateAgentRequest(BaseModel):
    """更新 Agent 请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    system_prompt: str | None = Field(default=None, max_length=10000)
    model_id: str | None = Field(default=None, max_length=200)
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=1, le=4096)
    runtime_type: str | None = Field(default=None, pattern=r"^(agent|basic)$")
    enable_teams: bool | None = Field(default=None)
    enable_memory: bool | None = Field(default=None)
    tool_ids: list[int] | None = Field(default=None, max_length=50)
