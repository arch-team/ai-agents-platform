"""Evaluation 模块测试配置和 Fixture。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.evaluation.application.services.evaluation_service import EvaluationService
from src.modules.evaluation.application.services.test_suite_service import TestSuiteService
from src.modules.evaluation.domain.entities.evaluation_result import EvaluationResult
from src.modules.evaluation.domain.entities.evaluation_run import EvaluationRun
from src.modules.evaluation.domain.entities.test_case import TestCase
from src.modules.evaluation.domain.entities.test_suite import TestSuite
from src.modules.evaluation.domain.repositories.evaluation_result_repository import (
    IEvaluationResultRepository,
)
from src.modules.evaluation.domain.repositories.evaluation_run_repository import (
    IEvaluationRunRepository,
)
from src.modules.evaluation.domain.repositories.test_case_repository import ITestCaseRepository
from src.modules.evaluation.domain.repositories.test_suite_repository import ITestSuiteRepository
from src.modules.evaluation.domain.value_objects.evaluation_run_status import EvaluationRunStatus
from src.modules.evaluation.domain.value_objects.test_suite_status import TestSuiteStatus


def make_test_suite(
    *,
    suite_id: int = 1,
    name: str = "测试集A",
    description: str = "测试描述",
    agent_id: int = 10,
    status: TestSuiteStatus = TestSuiteStatus.DRAFT,
    owner_id: int = 100,
) -> TestSuite:
    """创建测试用 TestSuite 实体。"""
    suite = TestSuite(
        name=name,
        description=description,
        agent_id=agent_id,
        status=status,
        owner_id=owner_id,
    )
    object.__setattr__(suite, "id", suite_id)
    return suite


def make_test_case(
    *,
    case_id: int = 1,
    suite_id: int = 1,
    input_prompt: str = "请回答以下问题",
    expected_output: str = "预期输出",
    evaluation_criteria: str = "评估标准",
    order_index: int = 0,
) -> TestCase:
    """创建测试用 TestCase 实体。"""
    case = TestCase(
        suite_id=suite_id,
        input_prompt=input_prompt,
        expected_output=expected_output,
        evaluation_criteria=evaluation_criteria,
        order_index=order_index,
    )
    object.__setattr__(case, "id", case_id)
    return case


def make_evaluation_run(
    *,
    run_id: int = 1,
    suite_id: int = 1,
    agent_id: int = 10,
    user_id: int = 100,
    status: EvaluationRunStatus = EvaluationRunStatus.PENDING,
    total_cases: int = 5,
    passed_cases: int = 0,
    failed_cases: int = 0,
    score: float = 0.0,
) -> EvaluationRun:
    """创建测试用 EvaluationRun 实体。"""
    run = EvaluationRun(
        suite_id=suite_id,
        agent_id=agent_id,
        user_id=user_id,
        status=status,
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        score=score,
    )
    object.__setattr__(run, "id", run_id)
    return run


def make_evaluation_result(
    *,
    result_id: int = 1,
    run_id: int = 1,
    case_id: int = 1,
    actual_output: str = "实际输出",
    score: float = 0.8,
    passed: bool = True,
    error_message: str = "",
) -> EvaluationResult:
    """创建测试用 EvaluationResult 实体。"""
    result = EvaluationResult(
        run_id=run_id,
        case_id=case_id,
        actual_output=actual_output,
        score=score,
        passed=passed,
        error_message=error_message,
    )
    object.__setattr__(result, "id", result_id)
    return result


@pytest.fixture
def mock_suite_repo() -> AsyncMock:
    """TestSuite 仓库 Mock。"""
    return AsyncMock(spec=ITestSuiteRepository)


@pytest.fixture
def mock_case_repo() -> AsyncMock:
    """TestCase 仓库 Mock。"""
    return AsyncMock(spec=ITestCaseRepository)


@pytest.fixture
def mock_run_repo() -> AsyncMock:
    """EvaluationRun 仓库 Mock。"""
    return AsyncMock(spec=IEvaluationRunRepository)


@pytest.fixture
def mock_result_repo() -> AsyncMock:
    """EvaluationResult 仓库 Mock。"""
    return AsyncMock(spec=IEvaluationResultRepository)


@pytest.fixture
def suite_service(
    mock_suite_repo: AsyncMock,
    mock_case_repo: AsyncMock,
) -> TestSuiteService:
    """TestSuiteService 实例（注入 mock 依赖）。"""
    return TestSuiteService(
        suite_repo=mock_suite_repo,
        case_repo=mock_case_repo,
    )


@pytest.fixture
def eval_service(
    mock_suite_repo: AsyncMock,
    mock_case_repo: AsyncMock,
    mock_run_repo: AsyncMock,
    mock_result_repo: AsyncMock,
) -> EvaluationService:
    """EvaluationService 实例（注入 mock 依赖）。"""
    return EvaluationService(
        suite_repo=mock_suite_repo,
        case_repo=mock_case_repo,
        run_repo=mock_run_repo,
        result_repo=mock_result_repo,
    )
