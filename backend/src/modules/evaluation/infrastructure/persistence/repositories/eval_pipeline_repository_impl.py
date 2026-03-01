"""EvalPipeline 仓储实现。"""

import json

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.domain.repositories.eval_pipeline_repository import IEvalPipelineRepository
from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus
from src.modules.evaluation.infrastructure.persistence.models.eval_pipeline_model import EvalPipelineModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class EvalPipelineRepositoryImpl(
    PydanticRepository[EvalPipeline, EvalPipelineModel, int],
    IEvalPipelineRepository,
):
    """EvalPipeline 仓储的 SQLAlchemy 实现。"""

    entity_class = EvalPipeline
    model_class = EvalPipelineModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "status",
            "bedrock_job_id",
            "score_summary_json",
            "error_message",
            "started_at",
            "completed_at",
            "updated_at",
        },
    )

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _to_model(self, entity: EvalPipeline) -> EvalPipelineModel:
        return EvalPipelineModel(
            id=entity.id,
            suite_id=entity.suite_id,
            agent_id=entity.agent_id,
            trigger=entity.trigger,
            model_ids_json=json.dumps(entity.model_ids),
            status=entity.status.value,
            bedrock_job_id=entity.bedrock_job_id,
            score_summary_json=json.dumps(entity.score_summary),
            error_message=entity.error_message,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, model: EvalPipelineModel) -> EvalPipeline:
        return EvalPipeline(
            id=model.id,
            suite_id=model.suite_id,
            agent_id=model.agent_id,
            trigger=model.trigger,
            model_ids=model.model_ids,
            status=PipelineStatus(model.status),
            bedrock_job_id=model.bedrock_job_id,
            score_summary=model.score_summary,
            error_message=model.error_message,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_by_suite(self, suite_id: int, limit: int = 20) -> list[EvalPipeline]:
        from sqlalchemy import select

        stmt = (
            select(EvalPipelineModel)
            .where(EvalPipelineModel.suite_id == suite_id)
            .order_by(EvalPipelineModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_running_by_suite(self, suite_id: int) -> EvalPipeline | None:
        from sqlalchemy import select

        stmt = select(EvalPipelineModel).where(
            EvalPipelineModel.suite_id == suite_id,
            EvalPipelineModel.status == PipelineStatus.RUNNING.value,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
