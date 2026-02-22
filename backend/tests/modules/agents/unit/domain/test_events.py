"""Agents 领域事件单元测试。"""

from uuid import UUID

import pytest

from src.modules.agents.domain.events import (
    AgentActivatedEvent,
    AgentArchivedEvent,
    AgentCreatedEvent,
    AgentDeletedEvent,
    AgentUpdatedEvent,
)
from src.shared.domain.events import DomainEvent


@pytest.mark.unit
class TestAgentCreatedEvent:
    def test_fields(self) -> None:
        event = AgentCreatedEvent(agent_id=1, owner_id=10, name="Test Agent")
        assert event.agent_id == 1
        assert event.owner_id == 10
        assert event.name == "Test Agent"

    def test_inherits_domain_event(self) -> None:
        assert issubclass(AgentCreatedEvent, DomainEvent)

    def test_has_event_id(self) -> None:
        event = AgentCreatedEvent(agent_id=1, owner_id=10, name="Test")
        assert isinstance(event.event_id, UUID)

    def test_has_occurred_at(self) -> None:
        event = AgentCreatedEvent(agent_id=1, owner_id=10, name="Test")
        assert event.occurred_at is not None


@pytest.mark.unit
class TestAgentActivatedEvent:
    def test_fields(self) -> None:
        event = AgentActivatedEvent(agent_id=1, owner_id=10)
        assert event.agent_id == 1
        assert event.owner_id == 10

    def test_inherits_domain_event(self) -> None:
        assert issubclass(AgentActivatedEvent, DomainEvent)


@pytest.mark.unit
class TestAgentArchivedEvent:
    def test_fields(self) -> None:
        event = AgentArchivedEvent(agent_id=1, owner_id=10)
        assert event.agent_id == 1
        assert event.owner_id == 10

    def test_inherits_domain_event(self) -> None:
        assert issubclass(AgentArchivedEvent, DomainEvent)


@pytest.mark.unit
class TestAgentUpdatedEvent:
    def test_fields(self) -> None:
        event = AgentUpdatedEvent(
            agent_id=1, owner_id=10, changed_fields=("name", "description"),
        )
        assert event.agent_id == 1
        assert event.owner_id == 10
        assert event.changed_fields == ("name", "description")

    def test_inherits_domain_event(self) -> None:
        assert issubclass(AgentUpdatedEvent, DomainEvent)


@pytest.mark.unit
class TestAgentDeletedEvent:
    def test_fields(self) -> None:
        event = AgentDeletedEvent(agent_id=1, owner_id=10)
        assert event.agent_id == 1
        assert event.owner_id == 10

    def test_inherits_domain_event(self) -> None:
        assert issubclass(AgentDeletedEvent, DomainEvent)
