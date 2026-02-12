"""评估运行仓库接口。"""

from abc import abstractmethod

from src.modules.evaluation.domain.entities.evaluation_run import EvaluationRun
from src.shared.domain.repositories import IRepository


class IEvaluationRunRepository(IRepository[EvaluationRun, int]):
    """评估运行仓库接口。"""

    @abstractmethod
    async def list_by_suite(
        self,
        suite_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[EvaluationRun]:
        """按测试集 ID 查询评估运行列表。"""

    @abstractmethod
    async def list_by_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[EvaluationRun]:
        """按用户 ID 查询评估运行列表。"""

    @abstractmethod
    async def count_by_user(self, user_id: int) -> int:
        """按用户 ID 统计评估运行数量。"""

    @abstractmethod
    async def count_by_suite(self, suite_id: int) -> int:
        """按测试集 ID 统计评估运行数量。"""
