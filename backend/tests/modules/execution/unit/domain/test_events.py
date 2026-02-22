"""Execution 领域事件单元测试。"""

from uuid import UUID

import pytest

from src.modules.execution.domain.events import (
    ConversationCompletedEvent,
    ConversationCreatedEvent,
    MessageReceivedEvent,
    MessageSentEvent,
)
from src.shared.domain.events import DomainEvent


@pytest.mark.unit
class TestConversationCreatedEvent:
    def test_fields(self) -> None:
        event = ConversationCreatedEvent(
            conversation_id=1, agent_id=5, user_id=10,
        )
        assert event.conversation_id == 1
        assert event.agent_id == 5
        assert event.user_id == 10

    def test_inherits_domain_event(self) -> None:
        assert issubclass(ConversationCreatedEvent, DomainEvent)

    def test_has_event_id(self) -> None:
        event = ConversationCreatedEvent(
            conversation_id=1, agent_id=5, user_id=10,
        )
        assert isinstance(event.event_id, UUID)

    def test_has_occurred_at(self) -> None:
        event = ConversationCreatedEvent(
            conversation_id=1, agent_id=5, user_id=10,
        )
        assert event.occurred_at is not None


@pytest.mark.unit
class TestMessageSentEvent:
    def test_fields(self) -> None:
        event = MessageSentEvent(
            conversation_id=1, message_id=10, user_id=5,
        )
        assert event.conversation_id == 1
        assert event.message_id == 10
        assert event.user_id == 5

    def test_inherits_domain_event(self) -> None:
        assert issubclass(MessageSentEvent, DomainEvent)


@pytest.mark.unit
class TestMessageReceivedEvent:
    def test_fields(self) -> None:
        event = MessageReceivedEvent(
            conversation_id=1,
            message_id=10,
            token_count=150,
            model_id="anthropic.claude-3-5-sonnet",
        )
        assert event.conversation_id == 1
        assert event.message_id == 10
        assert event.token_count == 150
        assert event.model_id == "anthropic.claude-3-5-sonnet"

    def test_inherits_domain_event(self) -> None:
        assert issubclass(MessageReceivedEvent, DomainEvent)


@pytest.mark.unit
class TestConversationCompletedEvent:
    def test_fields(self) -> None:
        event = ConversationCompletedEvent(conversation_id=1, user_id=10)
        assert event.conversation_id == 1
        assert event.user_id == 10

    def test_inherits_domain_event(self) -> None:
        assert issubclass(ConversationCompletedEvent, DomainEvent)
