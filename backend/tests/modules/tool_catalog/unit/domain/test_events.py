"""Tool Catalog 领域事件单元测试。"""

from uuid import UUID

import pytest

from src.modules.tool_catalog.domain.events import (
    ToolApprovedEvent,
    ToolCreatedEvent,
    ToolDeletedEvent,
    ToolDeprecatedEvent,
    ToolRejectedEvent,
    ToolSubmittedEvent,
    ToolUpdatedEvent,
)
from src.shared.domain.events import DomainEvent


@pytest.mark.unit
class TestToolCreatedEvent:
    def test_fields(self) -> None:
        event = ToolCreatedEvent(
            tool_id=1, creator_id=10, name="Test Tool", tool_type="mcp_server",
        )
        assert event.tool_id == 1
        assert event.creator_id == 10
        assert event.name == "Test Tool"
        assert event.tool_type == "mcp_server"

    def test_inherits_domain_event(self) -> None:
        assert issubclass(ToolCreatedEvent, DomainEvent)

    def test_has_event_id(self) -> None:
        event = ToolCreatedEvent(tool_id=1, creator_id=10, name="Test", tool_type="api")
        assert isinstance(event.event_id, UUID)

    def test_has_occurred_at(self) -> None:
        event = ToolCreatedEvent(tool_id=1, creator_id=10, name="Test", tool_type="api")
        assert event.occurred_at is not None


@pytest.mark.unit
class TestToolUpdatedEvent:
    def test_fields(self) -> None:
        event = ToolUpdatedEvent(
            tool_id=1, creator_id=10, changed_fields=("name", "description"),
        )
        assert event.tool_id == 1
        assert event.creator_id == 10
        assert event.changed_fields == ("name", "description")

    def test_inherits_domain_event(self) -> None:
        assert issubclass(ToolUpdatedEvent, DomainEvent)


@pytest.mark.unit
class TestToolDeletedEvent:
    def test_fields(self) -> None:
        event = ToolDeletedEvent(tool_id=1, creator_id=10)
        assert event.tool_id == 1
        assert event.creator_id == 10

    def test_inherits_domain_event(self) -> None:
        assert issubclass(ToolDeletedEvent, DomainEvent)


@pytest.mark.unit
class TestToolSubmittedEvent:
    def test_fields(self) -> None:
        event = ToolSubmittedEvent(tool_id=1, creator_id=10)
        assert event.tool_id == 1
        assert event.creator_id == 10

    def test_inherits_domain_event(self) -> None:
        assert issubclass(ToolSubmittedEvent, DomainEvent)


@pytest.mark.unit
class TestToolApprovedEvent:
    def test_fields(self) -> None:
        event = ToolApprovedEvent(tool_id=1, creator_id=10, reviewer_id=99)
        assert event.tool_id == 1
        assert event.creator_id == 10
        assert event.reviewer_id == 99

    def test_inherits_domain_event(self) -> None:
        assert issubclass(ToolApprovedEvent, DomainEvent)


@pytest.mark.unit
class TestToolRejectedEvent:
    def test_fields(self) -> None:
        event = ToolRejectedEvent(
            tool_id=1, creator_id=10, reviewer_id=99, comment="配置不完整",
        )
        assert event.tool_id == 1
        assert event.creator_id == 10
        assert event.reviewer_id == 99
        assert event.comment == "配置不完整"

    def test_inherits_domain_event(self) -> None:
        assert issubclass(ToolRejectedEvent, DomainEvent)


@pytest.mark.unit
class TestToolDeprecatedEvent:
    def test_fields(self) -> None:
        event = ToolDeprecatedEvent(tool_id=1, creator_id=10)
        assert event.tool_id == 1
        assert event.creator_id == 10

    def test_inherits_domain_event(self) -> None:
        assert issubclass(ToolDeprecatedEvent, DomainEvent)
