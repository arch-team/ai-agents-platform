"""团队执行仓库接口。"""

from abc import abstractmethod

from src.modules.execution.domain.entities.team_execution import TeamExecution
from src.modules.execution.domain.entities.team_execution_log import TeamExecutionLog
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
    ) -> list[TeamExecution]:
        """按用户 ID 获取执行列表，按 id DESC 排序。"""

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TeamExecution]:
        """按 Agent ID 获取执行列表，按 id DESC 排序。"""

    @abstractmethod
    async def count_by_user(self, user_id: int) -> int:
        """按用户 ID 统计执行数量。"""


class ITeamExecutionLogRepository(IRepository[TeamExecutionLog, int]):
    """团队执行日志仓库接口。"""

    @abstractmethod
    async def list_by_execution(
        self,
        execution_id: int,
        *,
        after_sequence: int = 0,
    ) -> list[TeamExecutionLog]:
        """按执行 ID 获取日志列表，按 sequence ASC 排序，可选过滤 sequence > after_sequence。"""

    @abstractmethod
    async def append_log(self, log: TeamExecutionLog) -> TeamExecutionLog:
        """追加执行日志。"""
