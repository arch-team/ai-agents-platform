"""跨模块 Agent 生命周期接口。

builder 模块依赖此接口管理 Agent 状态转换，
避免直接导入 agents 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod

from src.shared.domain.interfaces.agent_creator import CreatedAgentInfo


class IAgentLifecycle(ABC):
    """跨模块 Agent 生命周期管理接口 (ISP: 与 IAgentCreator 分离)。"""

    @abstractmethod
    async def start_testing(self, agent_id: int, operator_id: int) -> CreatedAgentInfo:
        """触发 Agent 进入 TESTING 状态 (创建 Runtime)。"""
        ...

    @abstractmethod
    async def go_live(self, agent_id: int, operator_id: int) -> CreatedAgentInfo:
        """触发 Agent 上线 (TESTING -> ACTIVE)。"""
        ...

    @abstractmethod
    async def take_offline(self, agent_id: int, operator_id: int) -> CreatedAgentInfo:
        """触发 Agent 下线 (ACTIVE -> ARCHIVED, 销毁 Runtime)。"""
        ...
