"""EvaluationResult 仓库实现。"""

from src.modules.evaluation.domain.entities.evaluation_result import EvaluationResult
from src.modules.evaluation.domain.repositories.evaluation_result_repository import (
    IEvaluationResultRepository,
)
from src.modules.evaluation.infrastructure.persistence.models.evaluation_result_model import (
    EvaluationResultModel,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class EvaluationResultRepositoryImpl(
    PydanticRepository[EvaluationResult, EvaluationResultModel, int],
    IEvaluationResultRepository,
):
    """EvaluationResult 仓库的 SQLAlchemy 实现。"""

    entity_class = EvaluationResult
    model_class = EvaluationResultModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "actual_output",
            "score",
            "passed",
            "error_message",
            "updated_at",
        },
    )

    async def list_by_run(
        self,
        run_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[EvaluationResult]:
        """按评估运行 ID 查询评估结果列表。"""
        return await self._list_where(
            EvaluationResultModel.run_id == run_id,
            offset=offset,
            limit=limit,
        )

    async def count_by_run(self, run_id: int) -> int:
        """按评估运行 ID 统计评估结果数量。"""
        return await self._count_where(EvaluationResultModel.run_id == run_id)
