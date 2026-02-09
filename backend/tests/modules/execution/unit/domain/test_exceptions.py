"""Execution 领域异常单元测试。"""

import pytest

from src.modules.execution.domain.exceptions import (
    AgentNotAvailableError,
    ConversationNotActiveError,
    ConversationNotFoundError,
    MessageNotFoundError,
)
from src.shared.domain.exceptions import DomainError, EntityNotFoundError


@pytest.mark.unit
class TestConversationNotFoundError:
    def test_message_contains_id(self) -> None:
        error = ConversationNotFoundError(conversation_id=42)
        assert "42" in error.message
        assert "Conversation" in error.message

    def test_inherits_entity_not_found_error(self) -> None:
        assert issubclass(ConversationNotFoundError, EntityNotFoundError)

    def test_error_code(self) -> None:
        error = ConversationNotFoundError(conversation_id=1)
        assert error.code == "NOT_FOUND_CONVERSATION"


@pytest.mark.unit
class TestMessageNotFoundError:
    def test_message_contains_id(self) -> None:
        error = MessageNotFoundError(message_id=99)
        assert "99" in error.message
        assert "Message" in error.message

    def test_inherits_entity_not_found_error(self) -> None:
        assert issubclass(MessageNotFoundError, EntityNotFoundError)

    def test_error_code(self) -> None:
        error = MessageNotFoundError(message_id=1)
        assert error.code == "NOT_FOUND_MESSAGE"


@pytest.mark.unit
class TestConversationNotActiveError:
    def test_message_contains_id(self) -> None:
        error = ConversationNotActiveError(conversation_id=7)
        assert "7" in error.message

    def test_inherits_domain_error(self) -> None:
        assert issubclass(ConversationNotActiveError, DomainError)

    def test_error_code(self) -> None:
        error = ConversationNotActiveError(conversation_id=1)
        assert error.code == "CONVERSATION_NOT_ACTIVE"


@pytest.mark.unit
class TestAgentNotAvailableError:
    def test_message_contains_id(self) -> None:
        error = AgentNotAvailableError(agent_id=3)
        assert "3" in error.message

    def test_inherits_domain_error(self) -> None:
        assert issubclass(AgentNotAvailableError, DomainError)

    def test_error_code(self) -> None:
        error = AgentNotAvailableError(agent_id=1)
        assert error.code == "AGENT_NOT_AVAILABLE"
