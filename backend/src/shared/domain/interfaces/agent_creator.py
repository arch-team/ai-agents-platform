"""跨模块 Agent 创建接口。

builder 模块依赖此接口创建 Agent，
避免直接导入 agents 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CreateAgentRequest:
    """创建 Agent 的跨模块传输对象（最小知识原则）。"""

    name: str
    system_prompt: str
    description: str = ""
    model_id: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class CreatedAgentInfo:
    """已创建 Agent 的跨模块传输对象。"""

    id: int
    name: str
    status: str


class IAgentCreator(ABC):
    """跨模块 Agent 创建接口。"""

    @abstractmethod
    async def create_agent(self, request: CreateAgentRequest, owner_id: int) -> CreatedAgentInfo: ...
