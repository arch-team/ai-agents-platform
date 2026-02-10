"""Conversation 实体单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.value_objects.conversation_status import (
    ConversationStatus,
)
from src.shared.domain.exceptions import InvalidStateTransitionError


@pytest.mark.unit
class TestConversationCreation:
    def test_create_conversation_with_defaults(self) -> None:
        conv = Conversation(agent_id=1, user_id=10)
        assert conv.title == ""
        assert conv.agent_id == 1
        assert conv.user_id == 10
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.message_count == 0
        assert conv.total_tokens == 0

    def test_create_conversation_with_title(self) -> None:
        conv = Conversation(agent_id=1, user_id=10, title="测试对话")
        assert conv.title == "测试对话"

    def test_create_conversation_inherits_pydantic_entity(self) -> None:
        conv = Conversation(agent_id=1, user_id=10)
        assert conv.id is None
        assert conv.created_at is not None
        assert conv.updated_at is not None

    @pytest.mark.parametrize(
        "field,kwargs",
        [
            ("title", {"agent_id": 1, "user_id": 10, "title": "A" * 201}),
            ("message_count", {"agent_id": 1, "user_id": 10, "message_count": -1}),
            ("total_tokens", {"agent_id": 1, "user_id": 10, "total_tokens": -1}),
        ],
        ids=["title_too_long", "negative_message_count", "negative_total_tokens"],
    )
    def test_field_validation_raises(self, field: str, kwargs: dict) -> None:
        with pytest.raises(ValidationError, match=field):
            Conversation(**kwargs)


@pytest.fixture
def active_conversation() -> Conversation:
    """活跃状态的 Conversation。"""
    return Conversation(agent_id=1, user_id=10)


@pytest.mark.unit
class TestConversationComplete:
    def test_complete_from_active_succeeds(
        self, active_conversation: Conversation
    ) -> None:
        active_conversation.complete()
        assert active_conversation.status == ConversationStatus.COMPLETED

    def test_complete_updates_timestamp(
        self, active_conversation: Conversation
    ) -> None:
        original = active_conversation.updated_at
        active_conversation.complete()
        assert active_conversation.updated_at is not None
        assert original is not None
        assert active_conversation.updated_at >= original

    @pytest.mark.parametrize(
        "setup_action",
        ["complete", "fail"],
        ids=["from_completed", "from_failed"],
    )
    def test_complete_from_terminal_state_raises(
        self, active_conversation: Conversation, setup_action: str
    ) -> None:
        getattr(active_conversation, setup_action)()
        with pytest.raises(InvalidStateTransitionError):
            active_conversation.complete()


@pytest.mark.unit
class TestConversationFail:
    def test_fail_from_active_succeeds(
        self, active_conversation: Conversation
    ) -> None:
        active_conversation.fail()
        assert active_conversation.status == ConversationStatus.FAILED

    def test_fail_updates_timestamp(
        self, active_conversation: Conversation
    ) -> None:
        original = active_conversation.updated_at
        active_conversation.fail()
        assert active_conversation.updated_at is not None
        assert original is not None
        assert active_conversation.updated_at >= original

    @pytest.mark.parametrize(
        "setup_action",
        ["complete", "fail"],
        ids=["from_completed", "from_failed"],
    )
    def test_fail_from_terminal_state_raises(
        self, active_conversation: Conversation, setup_action: str
    ) -> None:
        getattr(active_conversation, setup_action)()
        with pytest.raises(InvalidStateTransitionError):
            active_conversation.fail()


@pytest.mark.unit
class TestConversationAddMessageCount:
    def test_add_message_count_increments(
        self, active_conversation: Conversation
    ) -> None:
        active_conversation.add_message_count(token_count=100)
        assert active_conversation.message_count == 1
        assert active_conversation.total_tokens == 100

    def test_add_message_count_multiple_times(
        self, active_conversation: Conversation
    ) -> None:
        active_conversation.add_message_count(token_count=50)
        active_conversation.add_message_count(token_count=80)
        assert active_conversation.message_count == 2
        assert active_conversation.total_tokens == 130

    def test_add_message_count_zero_tokens(
        self, active_conversation: Conversation
    ) -> None:
        active_conversation.add_message_count(token_count=0)
        assert active_conversation.message_count == 1
        assert active_conversation.total_tokens == 0

    def test_add_message_count_updates_timestamp(
        self, active_conversation: Conversation
    ) -> None:
        original = active_conversation.updated_at
        active_conversation.add_message_count(token_count=10)
        assert active_conversation.updated_at is not None
        assert original is not None
        assert active_conversation.updated_at >= original

    @pytest.mark.parametrize(
        "setup_action",
        ["complete", "fail"],
        ids=["when_completed", "when_failed"],
    )
    def test_add_message_count_when_terminal_raises(
        self, active_conversation: Conversation, setup_action: str
    ) -> None:
        getattr(active_conversation, setup_action)()
        with pytest.raises(InvalidStateTransitionError):
            active_conversation.add_message_count(token_count=10)
