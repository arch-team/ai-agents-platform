"""Agent 配置值对象（frozen dataclass，不可变）。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """Agent 模型配置，不可变值对象。"""

    model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    stop_sequences: tuple[str, ...] = ()
