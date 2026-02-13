"""按 Agent 维度的 Token 消耗归因值对象。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentTokenBreakdown:
    """单个 Agent 的 Token 消耗聚合数据。"""

    agent_id: int
    agent_name: str
    total_tokens: int
    tokens_input: int
    tokens_output: int
    invocation_count: int
