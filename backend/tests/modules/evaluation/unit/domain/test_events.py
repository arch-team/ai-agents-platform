"""Evaluation 领域事件单元测试。"""

import pytest

from src.modules.evaluation.domain.events import (
    EvaluationRunCompletedEvent,
    TestSuiteActivatedEvent,
    TestSuiteArchivedEvent,
    TestSuiteCreatedEvent,
)
from src.shared.domain.events import DomainEvent


@pytest.mark.unit
class TestEvaluationEvents:
    """评估模块事件测试。"""

    def test_test_suite_created_event(self) -> None:
        event = TestSuiteCreatedEvent(suite_id=1, owner_id=10)
        assert isinstance(event, DomainEvent)
        assert event.suite_id == 1
        assert event.owner_id == 10
        assert event.event_id is not None
        assert event.occurred_at is not None

    def test_test_suite_activated_event(self) -> None:
        event = TestSuiteActivatedEvent(suite_id=2)
        assert event.suite_id == 2

    def test_test_suite_archived_event(self) -> None:
        event = TestSuiteArchivedEvent(suite_id=3)
        assert event.suite_id == 3

    def test_evaluation_run_completed_event(self) -> None:
        event = EvaluationRunCompletedEvent(
            run_id=1, suite_id=2, user_id=10, score=0.85,
        )
        assert event.run_id == 1
        assert event.suite_id == 2
        assert event.user_id == 10
        assert event.score == 0.85
