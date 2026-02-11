"""templates 领域事件测试。"""

import pytest

from src.modules.templates.domain.events import (
    TemplateArchivedEvent,
    TemplateCreatedEvent,
    TemplateInstantiatedEvent,
    TemplatePublishedEvent,
)
from src.shared.domain.events import DomainEvent


@pytest.mark.unit
class TestTemplateEvents:
    """模板领域事件测试。"""

    def test_created_event(self) -> None:
        event = TemplateCreatedEvent(template_id=1, creator_id=10)
        assert event.template_id == 1
        assert event.creator_id == 10
        assert isinstance(event, DomainEvent)

    def test_published_event(self) -> None:
        event = TemplatePublishedEvent(template_id=1)
        assert event.template_id == 1
        assert isinstance(event, DomainEvent)

    def test_archived_event(self) -> None:
        event = TemplateArchivedEvent(template_id=1)
        assert event.template_id == 1
        assert isinstance(event, DomainEvent)

    def test_instantiated_event(self) -> None:
        event = TemplateInstantiatedEvent(
            template_id=1,
            agent_id=100,
            instantiated_by=10,
        )
        assert event.template_id == 1
        assert event.agent_id == 100
        assert event.instantiated_by == 10
        assert isinstance(event, DomainEvent)

    def test_event_has_event_id(self) -> None:
        event = TemplateCreatedEvent(template_id=1, creator_id=10)
        assert event.event_id is not None

    def test_event_has_occurred_at(self) -> None:
        event = TemplateCreatedEvent(template_id=1, creator_id=10)
        assert event.occurred_at is not None
