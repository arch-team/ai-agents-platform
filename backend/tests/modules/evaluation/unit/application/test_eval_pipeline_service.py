"""EvalPipelineService 单元测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.evaluation.application.dto.pipeline_dto import EvalPipelineDTO, TriggerPipelineDTO
from src.modules.evaluation.application.interfaces.eval_service import IEvalService
from src.modules.evaluation.application.services.eval_pipeline_service import EvalPipelineService
from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.domain.exceptions import (
    EvalPipelineNotFoundError,
    PipelineAlreadyRunningError,
    TestSuiteNotFoundError,
)
from src.modules.evaluation.domain.repositories.eval_pipeline_repository import IEvalPipelineRepository
from src.modules.evaluation.domain.repositories.test_case_repository import ITestCaseRepository
from src.modules.evaluation.domain.repositories.test_suite_repository import ITestSuiteRepository
from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45
from tests.modules.evaluation.conftest import make_test_case, make_test_suite


def make_pipeline_entity(*, pipeline_id: int = 1) -> EvalPipeline:
    """创建测试用 EvalPipeline 实体。"""
    pipeline = EvalPipeline(
        suite_id=1,
        agent_id=1,
        trigger="manual",
        model_ids=[MODEL_CLAUDE_HAIKU_45],
    )
    object.__setattr__(pipeline, "id", pipeline_id)
    object.__setattr__(pipeline, "created_at", datetime.now(UTC))
    object.__setattr__(pipeline, "updated_at", datetime.now(UTC))
    return pipeline


@pytest.fixture
def mock_pipeline_repo() -> AsyncMock:
    """IEvalPipelineRepository Mock。"""
    return AsyncMock(spec=IEvalPipelineRepository)


@pytest.fixture
def mock_suite_repo() -> AsyncMock:
    """ITestSuiteRepository Mock。"""
    return AsyncMock(spec=ITestSuiteRepository)


@pytest.fixture
def mock_case_repo() -> AsyncMock:
    """ITestCaseRepository Mock。"""
    return AsyncMock(spec=ITestCaseRepository)


@pytest.fixture
def mock_eval_service() -> AsyncMock:
    """IEvalService Mock。"""
    return AsyncMock(spec=IEvalService)


@pytest.fixture
def service(
    mock_pipeline_repo: AsyncMock,
    mock_suite_repo: AsyncMock,
    mock_case_repo: AsyncMock,
    mock_eval_service: AsyncMock,
) -> EvalPipelineService:
    """EvalPipelineService 实例（注入 mock 依赖）。"""
    return EvalPipelineService(
        pipeline_repo=mock_pipeline_repo,
        suite_repo=mock_suite_repo,
        case_repo=mock_case_repo,
        eval_service=mock_eval_service,
    )


@pytest.mark.unit
class TestEvalPipelineServiceTrigger:
    """trigger 方法的单元测试。"""

    @pytest.mark.asyncio
    async def test_trigger_creates_pipeline(
        self,
        service: EvalPipelineService,
        mock_pipeline_repo: AsyncMock,
        mock_suite_repo: AsyncMock,
        mock_case_repo: AsyncMock,
        mock_eval_service: AsyncMock,
    ) -> None:
        """正常触发：验证 pipeline_repo.create 被调用，eval_service.create_eval_job 被调用，返回 EvalPipelineDTO。"""
        # Arrange
        suite = make_test_suite(suite_id=1, agent_id=10)
        cases = [make_test_case(case_id=1, suite_id=1)]
        pipeline = make_pipeline_entity(pipeline_id=42)

        mock_pipeline_repo.find_running_by_suite.return_value = None
        mock_suite_repo.get_by_id.return_value = suite
        mock_case_repo.list_by_suite.return_value = cases
        mock_pipeline_repo.create.return_value = pipeline
        mock_pipeline_repo.update.return_value = pipeline
        mock_eval_service.create_eval_job.return_value = "bedrock-job-001"

        dto = TriggerPipelineDTO(suite_id=1, agent_id=10)

        # Act
        result = await service.trigger(dto)

        # Assert
        mock_pipeline_repo.find_running_by_suite.assert_called_once_with(1)
        mock_suite_repo.get_by_id.assert_called_once_with(1)
        mock_case_repo.list_by_suite.assert_called_once_with(1)
        mock_pipeline_repo.create.assert_called_once()
        mock_eval_service.create_eval_job.assert_called_once()
        assert isinstance(result, EvalPipelineDTO)
        assert result.id == 42

    @pytest.mark.asyncio
    async def test_trigger_raises_if_already_running(
        self,
        service: EvalPipelineService,
        mock_pipeline_repo: AsyncMock,
    ) -> None:
        """find_running_by_suite 返回非 None 时抛出 PipelineAlreadyRunningError。"""
        # Arrange
        running_pipeline = make_pipeline_entity(pipeline_id=99)
        mock_pipeline_repo.find_running_by_suite.return_value = running_pipeline

        dto = TriggerPipelineDTO(suite_id=1, agent_id=10)

        # Act & Assert
        with pytest.raises(PipelineAlreadyRunningError):
            await service.trigger(dto)

        mock_pipeline_repo.find_running_by_suite.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_trigger_raises_if_suite_not_found(
        self,
        service: EvalPipelineService,
        mock_pipeline_repo: AsyncMock,
        mock_suite_repo: AsyncMock,
    ) -> None:
        """suite_repo.get_by_id 返回 None 时抛出 TestSuiteNotFoundError。"""
        # Arrange
        mock_pipeline_repo.find_running_by_suite.return_value = None
        mock_suite_repo.get_by_id.return_value = None

        dto = TriggerPipelineDTO(suite_id=999, agent_id=10)

        # Act & Assert
        with pytest.raises(TestSuiteNotFoundError):
            await service.trigger(dto)

        mock_suite_repo.get_by_id.assert_called_once_with(999)


@pytest.mark.unit
class TestEvalPipelineServiceGet:
    """get 方法的单元测试。"""

    @pytest.mark.asyncio
    async def test_get_returns_dto(
        self,
        service: EvalPipelineService,
        mock_pipeline_repo: AsyncMock,
    ) -> None:
        """正常获取：返回 EvalPipelineDTO。"""
        # Arrange
        pipeline = make_pipeline_entity(pipeline_id=5)
        mock_pipeline_repo.get_by_id.return_value = pipeline

        # Act
        result = await service.get(pipeline_id=5, user_id=100)

        # Assert
        mock_pipeline_repo.get_by_id.assert_called_once_with(5)
        assert isinstance(result, EvalPipelineDTO)
        assert result.id == 5

    @pytest.mark.asyncio
    async def test_get_raises_if_not_found(
        self,
        service: EvalPipelineService,
        mock_pipeline_repo: AsyncMock,
    ) -> None:
        """pipeline 不存在时抛出 EvalPipelineNotFoundError。"""
        # Arrange
        mock_pipeline_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(EvalPipelineNotFoundError):
            await service.get(pipeline_id=999, user_id=100)

        mock_pipeline_repo.get_by_id.assert_called_once_with(999)
