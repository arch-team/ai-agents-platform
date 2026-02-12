"""Evaluation 领域实体单元测试。"""

import pytest

from src.modules.evaluation.domain.entities.evaluation_result import EvaluationResult
from src.modules.evaluation.domain.entities.evaluation_run import EvaluationRun
from src.modules.evaluation.domain.entities.test_case import TestCase
from src.modules.evaluation.domain.entities.test_suite import TestSuite
from src.modules.evaluation.domain.value_objects.evaluation_run_status import EvaluationRunStatus
from src.modules.evaluation.domain.value_objects.test_suite_status import TestSuiteStatus
from src.shared.domain.exceptions import InvalidStateTransitionError


# -- TestSuite 实体测试 --

@pytest.mark.unit
class TestTestSuiteEntity:
    """TestSuite 实体测试。"""

    def test_create_with_defaults(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10)
        assert suite.name == "测试集"
        assert suite.description == ""
        assert suite.agent_id == 1
        assert suite.owner_id == 10
        assert suite.status == TestSuiteStatus.DRAFT

    def test_activate_from_draft(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10)
        suite.activate()
        assert suite.status == TestSuiteStatus.ACTIVE

    def test_activate_from_active_raises(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10, status=TestSuiteStatus.ACTIVE)
        with pytest.raises(InvalidStateTransitionError):
            suite.activate()

    def test_activate_from_archived_raises(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10, status=TestSuiteStatus.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError):
            suite.activate()

    def test_archive_from_draft(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10)
        suite.archive()
        assert suite.status == TestSuiteStatus.ARCHIVED

    def test_archive_from_active(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10, status=TestSuiteStatus.ACTIVE)
        suite.archive()
        assert suite.status == TestSuiteStatus.ARCHIVED

    def test_archive_from_archived_raises(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10, status=TestSuiteStatus.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError):
            suite.archive()

    def test_can_delete_draft(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10)
        assert suite.can_delete() is True

    def test_can_delete_active(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10, status=TestSuiteStatus.ACTIVE)
        assert suite.can_delete() is False

    def test_can_delete_archived(self) -> None:
        suite = TestSuite(name="测试集", agent_id=1, owner_id=10, status=TestSuiteStatus.ARCHIVED)
        assert suite.can_delete() is False


# -- TestCase 实体测试 --

@pytest.mark.unit
class TestTestCaseEntity:
    """TestCase 实体测试。"""

    def test_create_with_defaults(self) -> None:
        case = TestCase(suite_id=1, input_prompt="问题")
        assert case.suite_id == 1
        assert case.input_prompt == "问题"
        assert case.expected_output == ""
        assert case.evaluation_criteria == ""
        assert case.order_index == 0

    def test_create_with_all_fields(self) -> None:
        case = TestCase(
            suite_id=1,
            input_prompt="问题",
            expected_output="答案",
            evaluation_criteria="标准",
            order_index=5,
        )
        assert case.expected_output == "答案"
        assert case.evaluation_criteria == "标准"
        assert case.order_index == 5


# -- EvaluationRun 实体测试 --

@pytest.mark.unit
class TestEvaluationRunEntity:
    """EvaluationRun 实体测试。"""

    def test_create_with_defaults(self) -> None:
        run = EvaluationRun(suite_id=1, agent_id=10, user_id=100)
        assert run.status == EvaluationRunStatus.PENDING
        assert run.total_cases == 0
        assert run.passed_cases == 0
        assert run.failed_cases == 0
        assert run.score == 0.0
        assert run.started_at is None
        assert run.completed_at is None

    def test_start_from_pending(self) -> None:
        run = EvaluationRun(suite_id=1, agent_id=10, user_id=100)
        run.start()
        assert run.status == EvaluationRunStatus.RUNNING
        assert run.started_at is not None

    def test_start_from_running_raises(self) -> None:
        run = EvaluationRun(suite_id=1, agent_id=10, user_id=100, status=EvaluationRunStatus.RUNNING)
        with pytest.raises(InvalidStateTransitionError):
            run.start()

    def test_complete_from_running(self) -> None:
        run = EvaluationRun(suite_id=1, agent_id=10, user_id=100, status=EvaluationRunStatus.RUNNING)
        run.complete(passed=3, failed=2, score=0.6)
        assert run.status == EvaluationRunStatus.COMPLETED
        assert run.passed_cases == 3
        assert run.failed_cases == 2
        assert run.score == 0.6
        assert run.completed_at is not None

    def test_complete_from_pending_raises(self) -> None:
        run = EvaluationRun(suite_id=1, agent_id=10, user_id=100)
        with pytest.raises(InvalidStateTransitionError):
            run.complete(passed=3, failed=2, score=0.6)

    def test_fail_from_running(self) -> None:
        run = EvaluationRun(suite_id=1, agent_id=10, user_id=100, status=EvaluationRunStatus.RUNNING)
        run.fail()
        assert run.status == EvaluationRunStatus.FAILED
        assert run.completed_at is not None

    def test_fail_from_pending_raises(self) -> None:
        run = EvaluationRun(suite_id=1, agent_id=10, user_id=100)
        with pytest.raises(InvalidStateTransitionError):
            run.fail()

    def test_fail_from_completed_raises(self) -> None:
        run = EvaluationRun(suite_id=1, agent_id=10, user_id=100, status=EvaluationRunStatus.COMPLETED)
        with pytest.raises(InvalidStateTransitionError):
            run.fail()


# -- EvaluationResult 实体测试 --

@pytest.mark.unit
class TestEvaluationResultEntity:
    """EvaluationResult 实体测试。"""

    def test_create_with_defaults(self) -> None:
        result = EvaluationResult(run_id=1, case_id=1)
        assert result.actual_output == ""
        assert result.score == 0.0
        assert result.passed is False
        assert result.error_message == ""

    def test_create_with_all_fields(self) -> None:
        result = EvaluationResult(
            run_id=1,
            case_id=2,
            actual_output="输出",
            score=0.9,
            passed=True,
            error_message="",
        )
        assert result.run_id == 1
        assert result.case_id == 2
        assert result.actual_output == "输出"
        assert result.score == 0.9
        assert result.passed is True


# -- 枚举测试 --

@pytest.mark.unit
class TestValueObjects:
    """值对象测试。"""

    def test_test_suite_status_values(self) -> None:
        assert TestSuiteStatus.DRAFT == "draft"
        assert TestSuiteStatus.ACTIVE == "active"
        assert TestSuiteStatus.ARCHIVED == "archived"

    def test_evaluation_run_status_values(self) -> None:
        assert EvaluationRunStatus.PENDING == "pending"
        assert EvaluationRunStatus.RUNNING == "running"
        assert EvaluationRunStatus.COMPLETED == "completed"
        assert EvaluationRunStatus.FAILED == "failed"
