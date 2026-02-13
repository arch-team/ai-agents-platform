"""审计模块领域事件单元测试。"""

import pytest

from src.modules.audit.domain.events import AuditLogCreatedEvent


@pytest.mark.unit
class TestAuditLogCreatedEvent:
    def test_event_creation_with_defaults(self) -> None:
        event = AuditLogCreatedEvent()
        assert event.audit_log_id == 0
        assert event.action == ""
        assert event.category == ""
        assert event.actor_id == 0
        assert event.event_id is not None
        assert event.occurred_at is not None

    def test_event_creation_with_values(self) -> None:
        event = AuditLogCreatedEvent(
            audit_log_id=42,
            action="create",
            category="agent_management",
            actor_id=100,
        )
        assert event.audit_log_id == 42
        assert event.action == "create"
        assert event.category == "agent_management"
        assert event.actor_id == 100
