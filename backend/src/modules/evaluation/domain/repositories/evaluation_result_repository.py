"""评估结果仓库接口。"""

from abc import abstractmethod

from src.modules.evaluation.domain.entities.evaluation_result import EvaluationResult
from src.shared.domain.repositories import IRepository


class IEvaluationResultRepository(IRepository[EvaluationResult, int]):
    """评估结果仓库接口。"""

    @abstractmethod
    async def list_by_run(
        self,
        run_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[EvaluationResult]:
        """按评估运行 ID 查询评估结果列表。"""

    @abstractmethod
    async def count_by_run(self, run_id: int) -> int:
        """按评估运行 ID 统计评估结果数量。"""
