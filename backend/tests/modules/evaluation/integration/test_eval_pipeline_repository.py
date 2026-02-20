"""EvalPipelineRepositoryImpl 集成测试。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# 导入 FK 引用的模型，确保 Base.metadata.create_all 能创建所有相关表
from src.modules.agents.infrastructure.persistence.models.agent_model import AgentModel  # noqa: F401
from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus
from src.modules.evaluation.infrastructure.persistence.repositories.eval_pipeline_repository_impl import (
    EvalPipelineRepositoryImpl,
)


def make_pipeline() -> EvalPipeline:
    """创建测试用 EvalPipeline 实体。"""
    return EvalPipeline(
        suite_id=1,
        agent_id=1,
        trigger="manual",
        model_ids=["us.anthropic.claude-haiku-4-20250514-v1:0"],
    )


@pytest.mark.asyncio
class TestEvalPipelineRepositoryImpl:
    async def test_create_and_get(self, sqlite_session: AsyncSession) -> None:
        repo = EvalPipelineRepositoryImpl(sqlite_session)
        pipeline = make_pipeline()
        saved = await repo.create(pipeline)
        assert saved.id is not None

        fetched = await repo.get_by_id(saved.id)
        assert fetched is not None
        assert fetched.suite_id == 1
        assert fetched.trigger == "manual"
        assert fetched.status == PipelineStatus.SCHEDULED

    async def test_list_by_suite(self, sqlite_session: AsyncSession) -> None:
        repo = EvalPipelineRepositoryImpl(sqlite_session)
        for _ in range(3):
            await repo.create(make_pipeline())

        results = await repo.list_by_suite(suite_id=1)
        assert len(results) == 3

    async def test_find_running_by_suite_returns_none_when_no_running(self, sqlite_session: AsyncSession) -> None:
        repo = EvalPipelineRepositoryImpl(sqlite_session)
        result = await repo.find_running_by_suite(suite_id=99)
        assert result is None
