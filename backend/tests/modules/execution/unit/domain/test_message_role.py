"""MessageRole 枚举单元测试。"""

import pytest

from src.modules.execution.domain.value_objects.message_role import MessageRole


@pytest.mark.unit
class TestMessageRole:
    def test_user_value(self) -> None:
        assert MessageRole.USER == "user"

    def test_assistant_value(self) -> None:
        assert MessageRole.ASSISTANT == "assistant"

    def test_is_str_enum(self) -> None:
        assert isinstance(MessageRole.USER, str)

    def test_all_members(self) -> None:
        members = {r.value for r in MessageRole}
        assert members == {"user", "assistant"}
