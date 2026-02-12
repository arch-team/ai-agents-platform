"""Evaluation 领域异常单元测试。"""

import pytest

from src.modules.evaluation.domain.exceptions import (
    EvaluationError,
    EvaluationRunNotFoundError,
    TestCaseNotFoundError,
    TestSuiteEmptyError,
    TestSuiteNotActiveError,
    TestSuiteNotDeletableError,
    TestSuiteNotFoundError,
)
from src.shared.domain.exceptions import DomainError, EntityNotFoundError


@pytest.mark.unit
class TestEvaluationExceptions:
    """评估模块异常测试。"""

    def test_evaluation_error_is_domain_error(self) -> None:
        err = EvaluationError("测试错误")
        assert isinstance(err, DomainError)

    def test_test_suite_not_found(self) -> None:
        err = TestSuiteNotFoundError(42)
        assert isinstance(err, EntityNotFoundError)
        assert "42" in err.message
        assert err.entity_type == "TestSuite"

    def test_test_case_not_found(self) -> None:
        err = TestCaseNotFoundError(99)
        assert isinstance(err, EntityNotFoundError)
        assert "99" in err.message

    def test_evaluation_run_not_found(self) -> None:
        err = EvaluationRunNotFoundError(7)
        assert isinstance(err, EntityNotFoundError)
        assert "7" in err.message

    def test_test_suite_not_active(self) -> None:
        err = TestSuiteNotActiveError(5)
        assert err.code == "TEST_SUITE_NOT_ACTIVE"
        assert "5" in err.message

    def test_test_suite_empty(self) -> None:
        err = TestSuiteEmptyError(3)
        assert err.code == "TEST_SUITE_EMPTY"
        assert "3" in err.message

    def test_test_suite_not_deletable(self) -> None:
        err = TestSuiteNotDeletableError(8)
        assert err.code == "TEST_SUITE_NOT_DELETABLE"
        assert "8" in err.message
