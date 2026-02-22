"""EvaluationService 应用服务单元测试。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.evaluation.application.dto.evaluation_dto import (
    CreateEvaluationRunDTO,
    EvaluationRunDTO,
)
from src.modules.evaluation.application.services.evaluation_service import EvaluationService
from src.modules.evaluation.domain.exceptions import (
    EvaluationRunNotFoundError,
    TestSuiteNotActiveError,
    TestSuiteNotFoundError,
)
from src.modules.evaluation.domain.value_objects.evaluation_run_status import EvaluationRunStatus
from src.modules.evaluation.domain.value_objects.test_suite_status import TestSuiteStatus
from tests.modules.evaluation.conftest import (
    make_evaluation_result,
    make_evaluation_run,
    make_test_case,
    make_test_suite,
)


@pytest.mark.unit
class TestRunEvaluation:
    """run_evaluation 测试。"""

    @pytest.mark.asyncio
    async def test_runs_evaluation_successfully(
        self,
        eval_service: EvaluationService,
        mock_suite_repo: AsyncMock,
        mock_case_repo: AsyncMock,
        mock_run_repo: AsyncMock,
        mock_result_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite(status=TestSuiteStatus.ACTIVE)
        mock_case_repo.list_by_suite.return_value = [
            make_test_case(case_id=1),
            make_test_case(case_id=2),
        ]
        # create -> start -> complete
        created_run = make_evaluation_run(status=EvaluationRunStatus.PENDING)
        started_run = make_evaluation_run(status=EvaluationRunStatus.RUNNING)
        completed_run = make_evaluation_run(
            status=EvaluationRunStatus.COMPLETED, passed_cases=2, score=1.0,
        )
        mock_run_repo.create.return_value = created_run
        mock_run_repo.update.side_effect = [started_run, completed_run]

        dto = CreateEvaluationRunDTO(suite_id=1)

        with patch("src.modules.evaluation.application.services.evaluation_service.event_bus") as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await eval_service.run_evaluation(dto, current_user_id=100)

        assert isinstance(result, EvaluationRunDTO)
        assert result.status == "completed"
        assert mock_result_repo.create.call_count == 2

    @pytest.mark.asyncio
    async def test_run_on_inactive_suite_raises(
        self,
        eval_service: EvaluationService,
        mock_suite_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = make_test_suite(status=TestSuiteStatus.DRAFT)
        dto = CreateEvaluationRunDTO(suite_id=1)
        with pytest.raises(TestSuiteNotActiveError):
            await eval_service.run_evaluation(dto, current_user_id=100)

    @pytest.mark.asyncio
    async def test_run_on_nonexistent_suite_raises(
        self,
        eval_service: EvaluationService,
        mock_suite_repo: AsyncMock,
    ) -> None:
        mock_suite_repo.get_by_id.return_value = None
        dto = CreateEvaluationRunDTO(suite_id=999)
        with pytest.raises(TestSuiteNotFoundError):
            await eval_service.run_evaluation(dto, current_user_id=100)


@pytest.mark.unit
class TestGetRun:
    """get_run 测试。"""

    @pytest.mark.asyncio
    async def test_returns_run_dto(
        self,
        eval_service: EvaluationService,
        mock_run_repo: AsyncMock,
    ) -> None:
        mock_run_repo.get_by_id.return_value = make_evaluation_run()
        result = await eval_service.get_run(1)
        assert isinstance(result, EvaluationRunDTO)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_not_found_raises(
        self,
        eval_service: EvaluationService,
        mock_run_repo: AsyncMock,
    ) -> None:
        mock_run_repo.get_by_id.return_value = None
        with pytest.raises(EvaluationRunNotFoundError):
            await eval_service.get_run(999)


@pytest.mark.unit
class TestListRuns:
    """list_runs 测试。"""

    @pytest.mark.asyncio
    async def test_lists_by_user(
        self,
        eval_service: EvaluationService,
        mock_run_repo: AsyncMock,
    ) -> None:
        mock_run_repo.list_by_user.return_value = [make_evaluation_run()]
        mock_run_repo.count_by_user.return_value = 1
        result = await eval_service.list_runs(100)
        assert len(result.items) == 1
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_lists_by_suite(
        self,
        eval_service: EvaluationService,
        mock_run_repo: AsyncMock,
    ) -> None:
        mock_run_repo.list_by_suite.return_value = [make_evaluation_run()]
        mock_run_repo.count_by_suite.return_value = 1
        result = await eval_service.list_runs(100, suite_id=1)
        assert len(result.items) == 1


@pytest.mark.unit
class TestGetResults:
    """get_results 测试。"""

    @pytest.mark.asyncio
    async def test_returns_results(
        self,
        eval_service: EvaluationService,
        mock_run_repo: AsyncMock,
        mock_result_repo: AsyncMock,
    ) -> None:
        mock_run_repo.get_by_id.return_value = make_evaluation_run()
        mock_result_repo.list_by_run.return_value = [make_evaluation_result()]
        mock_result_repo.count_by_run.return_value = 1
        result = await eval_service.get_results(1)
        assert len(result.items) == 1
        assert result.items[0].score == 0.8

    @pytest.mark.asyncio
    async def test_results_for_nonexistent_run_raises(
        self,
        eval_service: EvaluationService,
        mock_run_repo: AsyncMock,
    ) -> None:
        mock_run_repo.get_by_id.return_value = None
        with pytest.raises(EvaluationRunNotFoundError):
            await eval_service.get_results(999)
