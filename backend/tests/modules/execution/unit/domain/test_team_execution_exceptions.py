"""团队执行领域异常单元测试。"""

import pytest

from src.modules.execution.domain.exceptions import (
    TeamExecutionNotCancellableError,
    TeamExecutionNotFoundError,
)
from src.shared.domain.exceptions import DomainError, EntityNotFoundError


@pytest.mark.unit
class TestTeamExecutionNotFoundError:
    """TeamExecutionNotFoundError 测试。"""

    def test_message_contains_id(self) -> None:
        """验证错误信息包含 entity_type 和 entity_id。"""
        error = TeamExecutionNotFoundError(execution_id=42)
        assert "42" in error.message
        assert "TeamExecution" in error.message

    def test_inherits_entity_not_found_error(self) -> None:
        assert issubclass(TeamExecutionNotFoundError, EntityNotFoundError)

    def test_error_code(self) -> None:
        error = TeamExecutionNotFoundError(execution_id=1)
        assert error.code == "NOT_FOUND_TEAMEXECUTION"

    def test_entity_type_and_id(self) -> None:
        """验证 entity_type 和 entity_id 属性。"""
        error = TeamExecutionNotFoundError(execution_id=99)
        assert error.entity_type == "TeamExecution"
        assert error.entity_id == 99


@pytest.mark.unit
class TestTeamExecutionNotCancellableError:
    """TeamExecutionNotCancellableError 测试。"""

    def test_message_contains_id(self) -> None:
        """验证错误信息包含执行 ID。"""
        error = TeamExecutionNotCancellableError(execution_id=7)
        assert "7" in error.message

    def test_inherits_domain_error(self) -> None:
        assert issubclass(TeamExecutionNotCancellableError, DomainError)

    def test_error_code(self) -> None:
        """验证 error code。"""
        error = TeamExecutionNotCancellableError(execution_id=1)
        assert error.code == "TEAM_EXECUTION_NOT_CANCELLABLE"
