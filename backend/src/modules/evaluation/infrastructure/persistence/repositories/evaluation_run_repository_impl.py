"""EvaluationRun 仓库实现。"""

from src.modules.evaluation.domain.entities.evaluation_run import EvaluationRun
from src.modules.evaluation.domain.repositories.evaluation_run_repository import (
    IEvaluationRunRepository,
)
from src.modules.evaluation.domain.value_objects.evaluation_run_status import EvaluationRunStatus
from src.modules.evaluation.infrastructure.persistence.models.evaluation_run_model import (
    EvaluationRunModel,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class EvaluationRunRepositoryImpl(
    PydanticRepository[EvaluationRun, EvaluationRunModel, int],
    IEvaluationRunRepository,
):
    """EvaluationRun 仓库的 SQLAlchemy 实现。"""

    entity_class = EvaluationRun
    model_class = EvaluationRunModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "status",
            "total_cases",
            "passed_cases",
            "failed_cases",
            "score",
            "started_at",
            "completed_at",
            "updated_at",
        },
    )

    def _to_entity(self, model: EvaluationRunModel) -> EvaluationRun:
        return EvaluationRun(
            id=model.id,
            suite_id=model.suite_id,
            agent_id=model.agent_id,
            user_id=model.user_id,
            status=EvaluationRunStatus(model.status),
            total_cases=model.total_cases,
            passed_cases=model.passed_cases,
            failed_cases=model.failed_cases,
            score=model.score,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _get_update_data(self, entity: EvaluationRun) -> dict[str, object]:
        return {
            "status": entity.status.value,
            "total_cases": entity.total_cases,
            "passed_cases": entity.passed_cases,
            "failed_cases": entity.failed_cases,
            "score": entity.score,
            "started_at": entity.started_at,
            "completed_at": entity.completed_at,
            "updated_at": entity.updated_at,
        }

    async def list_by_suite(self, suite_id: int, *, offset: int = 0, limit: int = 20) -> list[EvaluationRun]:
        return await self._list_where(EvaluationRunModel.suite_id == suite_id, offset=offset, limit=limit)

    async def list_by_user(self, user_id: int, *, offset: int = 0, limit: int = 20) -> list[EvaluationRun]:
        return await self._list_where(EvaluationRunModel.user_id == user_id, offset=offset, limit=limit)

    async def count_by_user(self, user_id: int) -> int:
        return await self._count_where(EvaluationRunModel.user_id == user_id)

    async def count_by_suite(self, suite_id: int) -> int:
        return await self._count_where(EvaluationRunModel.suite_id == suite_id)
