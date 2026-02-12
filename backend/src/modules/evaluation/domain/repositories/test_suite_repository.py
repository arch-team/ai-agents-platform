"""测试集仓库接口。"""

from abc import abstractmethod

from src.modules.evaluation.domain.entities.test_suite import TestSuite
from src.shared.domain.repositories import IRepository


class ITestSuiteRepository(IRepository[TestSuite, int]):
    """测试集仓库接口。"""

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TestSuite]:
        """按 Agent ID 查询测试集列表。"""

    @abstractmethod
    async def count_by_agent(self, agent_id: int) -> int:
        """按 Agent ID 统计测试集数量。"""
