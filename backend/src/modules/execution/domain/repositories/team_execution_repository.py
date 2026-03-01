"""团队执行仓库接口。"""

from abc import abstractmethod

from src.modules.execution.domain.entities.team_execution import TeamExecution
from src.modules.execution.domain.entities.team_execution_log import TeamExecutionLog
from src.modules.execution.domain.value_objects.team_execution_status import TeamExecutionStatus
from src.shared.domain.repositories import IRepository


class ITeamExecutionRepository(IRepository[TeamExecution, int]):
    """团队执行仓库接口。"""

    @abstractmethod
    async def list_by_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TeamExecution]: ...

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TeamExecution]: ...

    @abstractmethod
    async def count_by_user(self, user_id: int) -> int: ...

    @abstractmethod
    async def list_by_statuses(self, statuses: list[TeamExecutionStatus]) -> list[TeamExecution]: ...


class ITeamExecutionLogRepository(IRepository[TeamExecutionLog, int]):
    """团队执行日志仓库接口。"""

    @abstractmethod
    async def list_by_execution(
        self,
        execution_id: int,
        *,
        after_sequence: int = 0,
    ) -> list[TeamExecutionLog]: ...

    @abstractmethod
    async def append_log(self, log: TeamExecutionLog) -> TeamExecutionLog: ...
