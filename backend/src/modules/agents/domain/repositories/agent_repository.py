"""Agent 仓库接口。"""

from abc import abstractmethod

from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.repositories import IRepository


class IAgentRepository(IRepository[Agent, int]):
    """Agent 仓库接口。"""

    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Agent]: ...

    @abstractmethod
    async def count_by_owner(self, owner_id: int) -> int: ...

    @abstractmethod
    async def get_by_name_and_owner(
        self,
        name: str,
        owner_id: int,
    ) -> Agent | None: ...

    @abstractmethod
    async def list_by_owner_and_status(
        self,
        owner_id: int,
        status: AgentStatus,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Agent]: ...

    @abstractmethod
    async def count_by_owner_and_status(
        self,
        owner_id: int,
        status: AgentStatus,
    ) -> int: ...
