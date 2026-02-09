"""ConversationStatus 枚举单元测试。"""

import pytest

from src.modules.execution.domain.value_objects.conversation_status import (
    ConversationStatus,
)


@pytest.mark.unit
class TestConversationStatus:
    def test_active_value(self) -> None:
        assert ConversationStatus.ACTIVE == "active"

    def test_completed_value(self) -> None:
        assert ConversationStatus.COMPLETED == "completed"

    def test_failed_value(self) -> None:
        assert ConversationStatus.FAILED == "failed"

    def test_is_str_enum(self) -> None:
        assert isinstance(ConversationStatus.ACTIVE, str)

    def test_all_members(self) -> None:
        members = {s.value for s in ConversationStatus}
        assert members == {"active", "completed", "failed"}
