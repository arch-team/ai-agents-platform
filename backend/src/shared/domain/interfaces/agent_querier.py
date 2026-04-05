"""跨模块 Agent 查询接口。

execution 模块依赖此接口获取 Agent 执行所需信息，
避免直接导入 agents 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ActiveAgentInfo:
    """跨模块传递的 Agent 执行信息（最小知识原则）。"""

    id: int
    name: str
    system_prompt: str
    model_id: str
    temperature: float
    max_tokens: int
    top_p: float
    stop_sequences: tuple[str, ...] = ()
    runtime_type: str = "agent"
    enable_teams: bool = False
    tool_ids: tuple[int, ...] = ()
    enable_memory: bool = False
    knowledge_base_id: int | None = None
    # Blueprint 扩展字段 (三模式路由用)
    workspace_path: str = ""
    runtime_arn: str = ""
    workspace_s3_uri: str = ""


class IAgentQuerier(ABC):
    """跨模块 Agent 查询接口。"""

    @abstractmethod
    async def get_active_agent(self, agent_id: int) -> ActiveAgentInfo | None: ...
