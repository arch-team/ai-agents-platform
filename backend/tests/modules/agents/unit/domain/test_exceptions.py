"""Agents 领域异常单元测试。"""

import pytest

from src.modules.agents.domain.exceptions import (
    AgentNameDuplicateError,
    AgentNotFoundError,
)
from src.shared.domain.exceptions import DuplicateEntityError, EntityNotFoundError


@pytest.mark.unit
class TestAgentNotFoundError:
    def test_message_contains_id(self) -> None:
        error = AgentNotFoundError(agent_id=42)
        assert "42" in error.message
        assert "Agent" in error.message

    def test_inherits_entity_not_found_error(self) -> None:
        assert issubclass(AgentNotFoundError, EntityNotFoundError)

    def test_error_code(self) -> None:
        error = AgentNotFoundError(agent_id=1)
        assert error.code == "NOT_FOUND_AGENT"


@pytest.mark.unit
class TestAgentNameDuplicateError:
    def test_message_contains_name(self) -> None:
        error = AgentNameDuplicateError(name="My Agent")
        assert "My Agent" in error.message
        assert "Agent" in error.message

    def test_inherits_duplicate_entity_error(self) -> None:
        assert issubclass(AgentNameDuplicateError, DuplicateEntityError)

    def test_error_code(self) -> None:
        error = AgentNameDuplicateError(name="My Agent")
        assert error.code == "DUPLICATE_AGENT"
