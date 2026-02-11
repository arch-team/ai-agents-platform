"""Agent 相关 DTO。"""

from dataclasses import dataclass
from datetime import datetime

from src.shared.domain.constants import (
    AGENT_DEFAULT_MAX_TOKENS,
    AGENT_DEFAULT_MODEL_ID,
    AGENT_DEFAULT_RUNTIME_TYPE,
    AGENT_DEFAULT_TEMPERATURE,
)


@dataclass
class CreateAgentDTO:
    """创建 Agent 请求数据。"""

    name: str
    description: str = ""
    system_prompt: str = ""
    model_id: str = AGENT_DEFAULT_MODEL_ID
    temperature: float = AGENT_DEFAULT_TEMPERATURE
    max_tokens: int = AGENT_DEFAULT_MAX_TOKENS
    runtime_type: str = AGENT_DEFAULT_RUNTIME_TYPE


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
