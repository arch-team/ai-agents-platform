"""跨模块 Agent 查询接口。

execution 模块依赖此接口获取 Agent 执行所需信息，
避免直接导入 agents 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ActiveAgentInfo:
    """跨模块传递的 Agent 执行信息（最小知识原则）。

    仅包含 execution 模块执行对话所需的字段，
    不暴露 Agent 的完整属性（如 description, status 等）。
    """

    id: int
    name: str
    system_prompt: str
    model_id: str
    temperature: float
    max_tokens: int
    top_p: float
    stop_sequences: tuple[str, ...] = ()
    knowledge_base_id: int | None = None


class IAgentQuerier(ABC):
    """跨模块 Agent 查询接口。

    接口定义在 shared/domain/interfaces/，
    实现由 agents 模块在 infrastructure 层提供。
    execution 模块的 Application 层依赖此接口。
    """

    @abstractmethod
    async def get_active_agent(self, agent_id: int) -> ActiveAgentInfo | None:
        """获取 ACTIVE 状态的 Agent 执行信息。

        Args:
            agent_id: Agent ID

        Returns:
            ActiveAgentInfo 如果 Agent 存在且为 ACTIVE 状态，否则 None。
        """
