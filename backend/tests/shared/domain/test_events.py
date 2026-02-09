"""DomainEvent 基类测试。"""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.shared.domain.events import DomainEvent


@pytest.mark.unit
class TestDomainEvent:
    """DomainEvent 基类测试。"""

    def test_event_has_unique_id(self) -> None:
        """每个事件实例有唯一的 event_id (UUID)。"""
        # Arrange & Act
        event = DomainEvent()

        # Assert
        assert isinstance(event.event_id, UUID)

    def test_event_has_occurred_at_timestamp(self) -> None:
        """事件自动记录 occurred_at 时间戳。"""
        # Arrange
        before = datetime.now(timezone.utc)

        # Act
        event = DomainEvent()

        # Assert
        after = datetime.now(timezone.utc)
        assert isinstance(event.occurred_at, datetime)
        assert before <= event.occurred_at <= after
        assert event.occurred_at.tzinfo is not None

    def test_event_has_correlation_id(self) -> None:
        """事件可接收 correlation_id 用于链路追踪。"""
        # Arrange
        correlation_id = "req-abc-123"

        # Act
        event = DomainEvent(correlation_id=correlation_id)

        # Assert
        assert event.correlation_id == correlation_id

    def test_event_default_correlation_id_is_none(self) -> None:
        """correlation_id 默认为 None。"""
        # Arrange & Act
        event = DomainEvent()

        # Assert
        assert event.correlation_id is None

    def test_different_events_have_different_ids(self) -> None:
        """不同事件实例有不同的 event_id。"""
        # Arrange & Act
        event1 = DomainEvent()
        event2 = DomainEvent()

        # Assert
        assert event1.event_id != event2.event_id
