"""Agent 配置值对象（frozen dataclass，不可变）。"""

from dataclasses import dataclass

from src.shared.domain.constants import (
    AGENT_DEFAULT_ENABLE_TEAMS,
    AGENT_DEFAULT_MAX_TOKENS,
    AGENT_DEFAULT_MODEL_ID,
    AGENT_DEFAULT_RUNTIME_TYPE,
    AGENT_DEFAULT_TEMPERATURE,
    AGENT_DEFAULT_TOP_P,
)


@dataclass(frozen=True)
class AgentConfig:
    """Agent 模型配置，不可变值对象。"""

    model_id: str = AGENT_DEFAULT_MODEL_ID
    temperature: float = AGENT_DEFAULT_TEMPERATURE
    max_tokens: int = AGENT_DEFAULT_MAX_TOKENS
    top_p: float = AGENT_DEFAULT_TOP_P
    stop_sequences: tuple[str, ...] = ()
    runtime_type: str = AGENT_DEFAULT_RUNTIME_TYPE
    enable_teams: bool = AGENT_DEFAULT_ENABLE_TEAMS
    enable_memory: bool = False
    tool_ids: tuple[int, ...] = ()
