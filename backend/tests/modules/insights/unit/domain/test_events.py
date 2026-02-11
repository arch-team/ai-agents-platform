"""insights 领域事件测试。"""

import pytest

from src.modules.insights.domain.events import UsageRecordCreatedEvent
from src.shared.domain.events import DomainEvent


@pytest.mark.unit
class TestUsageRecordEvents:
    """UsageRecord 事件测试。"""

    def test_created_event(self) -> None:
        event = UsageRecordCreatedEvent(
            record_id=1,
            user_id=10,
            agent_id=5,
            estimated_cost=0.015,
        )
        assert event.record_id == 1
        assert event.user_id == 10
        assert event.agent_id == 5
        assert event.estimated_cost == 0.015
        assert isinstance(event, DomainEvent)

    def test_created_event_has_event_id(self) -> None:
        event = UsageRecordCreatedEvent(
            record_id=1,
            user_id=10,
            agent_id=5,
            estimated_cost=0.015,
        )
        assert event.event_id is not None

    def test_created_event_has_occurred_at(self) -> None:
        event = UsageRecordCreatedEvent(
            record_id=1,
            user_id=10,
            agent_id=5,
            estimated_cost=0.015,
        )
        assert event.occurred_at is not None
