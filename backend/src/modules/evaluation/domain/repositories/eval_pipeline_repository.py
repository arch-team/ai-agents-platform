"""Eval Pipeline 仓储接口。"""

from abc import abstractmethod

from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.shared.domain.repositories import IRepository


class IEvalPipelineRepository(IRepository[EvalPipeline, int]):
    """Eval Pipeline 仓储接口。"""

    @abstractmethod
    async def list_by_suite(self, suite_id: int, limit: int = 20) -> list[EvalPipeline]:
        """查询指定 TestSuite 的最近 Pipeline 列表。"""
        ...

    @abstractmethod
    async def find_running_by_suite(self, suite_id: int) -> EvalPipeline | None:
        """查询正在运行的 Pipeline（防止重复触发）。"""
        ...
