"""团队执行领域事件单元测试。"""

from uuid import UUID

import pytest

from src.modules.execution.domain.events import (
    TeamExecutionCompletedEvent,
    TeamExecutionFailedEvent,
    TeamExecutionStartedEvent,
)
from src.shared.domain.constants import MODEL_CLAUDE_SONNET_46
from src.shared.domain.events import DomainEvent


@pytest.mark.unit
class TestTeamExecutionStartedEvent:
    """TeamExecutionStartedEvent 测试。"""

    def test_started_event_fields(self) -> None:
        """验证 execution_id, agent_id, user_id。"""
        event = TeamExecutionStartedEvent(
            execution_id=1,
            agent_id=5,
            user_id=10,
        )
        assert event.execution_id == 1
        assert event.agent_id == 5
        assert event.user_id == 10

    def test_inherits_domain_event(self) -> None:
        assert issubclass(TeamExecutionStartedEvent, DomainEvent)

    def test_has_event_id(self) -> None:
        event = TeamExecutionStartedEvent(
            execution_id=1,
            agent_id=5,
            user_id=10,
        )
        assert isinstance(event.event_id, UUID)

    def test_has_occurred_at(self) -> None:
        event = TeamExecutionStartedEvent(
            execution_id=1,
            agent_id=5,
            user_id=10,
        )
        assert event.occurred_at is not None


@pytest.mark.unit
class TestTeamExecutionCompletedEvent:
    """TeamExecutionCompletedEvent 测试。"""

    def test_completed_event_fields(self) -> None:
        """验证 execution_id, user_id, input_tokens, output_tokens, model_id。"""
        event = TeamExecutionCompletedEvent(
            execution_id=1,
            user_id=10,
            input_tokens=100,
            output_tokens=200,
            model_id=MODEL_CLAUDE_SONNET_46,
        )
        assert event.execution_id == 1
        assert event.user_id == 10
        assert event.input_tokens == 100
        assert event.output_tokens == 200
        assert event.model_id == MODEL_CLAUDE_SONNET_46

    def test_inherits_domain_event(self) -> None:
        assert issubclass(TeamExecutionCompletedEvent, DomainEvent)

    def test_default_token_values(self) -> None:
        """验证 token 和 model_id 默认值。"""
        event = TeamExecutionCompletedEvent(execution_id=1, user_id=10)
        assert event.input_tokens == 0
        assert event.output_tokens == 0
        assert event.model_id == ""


@pytest.mark.unit
class TestTeamExecutionFailedEvent:
    """TeamExecutionFailedEvent 测试。"""

    def test_failed_event_fields(self) -> None:
        """验证 execution_id, user_id, error_message。"""
        event = TeamExecutionFailedEvent(
            execution_id=1,
            user_id=10,
            error_message="超时错误",
        )
        assert event.execution_id == 1
        assert event.user_id == 10
        assert event.error_message == "超时错误"

    def test_inherits_domain_event(self) -> None:
        assert issubclass(TeamExecutionFailedEvent, DomainEvent)

    def test_default_error_message(self) -> None:
        """验证 error_message 默认值为空字符串。"""
        event = TeamExecutionFailedEvent(execution_id=1, user_id=10)
        assert event.error_message == ""
