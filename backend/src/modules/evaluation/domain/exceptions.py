"""evaluation 模块领域异常。"""

from src.shared.domain.exceptions import DomainError, EntityNotFoundError


class EvaluationError(DomainError):
    """评估模块基础异常。"""


class TestSuiteNotFoundError(EvaluationError, EntityNotFoundError):
    """测试集不存在。"""

    def __init__(self, suite_id: int) -> None:
        EntityNotFoundError.__init__(self, entity_type="TestSuite", entity_id=suite_id)


class TestCaseNotFoundError(EvaluationError, EntityNotFoundError):
    """测试用例不存在。"""

    def __init__(self, case_id: int) -> None:
        EntityNotFoundError.__init__(self, entity_type="TestCase", entity_id=case_id)


class EvaluationRunNotFoundError(EvaluationError, EntityNotFoundError):
    """评估运行不存在。"""

    def __init__(self, run_id: int) -> None:
        EntityNotFoundError.__init__(self, entity_type="EvaluationRun", entity_id=run_id)


class TestSuiteNotActiveError(EvaluationError):
    """测试集未激活，无法执行评估。"""

    def __init__(self, suite_id: int) -> None:
        super().__init__(
            message=f"TestSuite(id={suite_id}) 未激活, 无法执行评估",
            code="TEST_SUITE_NOT_ACTIVE",
        )


class TestSuiteEmptyError(EvaluationError):
    """测试集无测试用例，无法激活。"""

    def __init__(self, suite_id: int) -> None:
        super().__init__(
            message=f"TestSuite(id={suite_id}) 无测试用例, 无法激活",
            code="TEST_SUITE_EMPTY",
        )


class TestSuiteNotDeletableError(EvaluationError):
    """测试集不可删除（非 DRAFT 状态）。"""

    def __init__(self, suite_id: int) -> None:
        super().__init__(
            message=f"TestSuite(id={suite_id}) 非 DRAFT 状态, 不可删除",
            code="TEST_SUITE_NOT_DELETABLE",
        )
