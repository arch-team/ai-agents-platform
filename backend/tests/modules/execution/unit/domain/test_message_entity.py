"""Message 实体单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.execution.domain.entities.message import Message
from src.modules.execution.domain.value_objects.message_role import MessageRole


@pytest.mark.unit
class TestMessageCreation:
    def test_create_message_with_defaults(self) -> None:
        message = Message(conversation_id=1, role=MessageRole.USER)
        assert message.conversation_id == 1
        assert message.role == MessageRole.USER
        assert message.content == ""
        assert message.token_count == 0

    def test_create_message_with_content(self) -> None:
        message = Message(
            conversation_id=1,
            role=MessageRole.ASSISTANT,
            content="你好，有什么可以帮你的？",
            token_count=15,
        )
        assert message.content == "你好，有什么可以帮你的？"
        assert message.token_count == 15
        assert message.role == MessageRole.ASSISTANT

    def test_create_message_inherits_pydantic_entity(self) -> None:
        message = Message(conversation_id=1, role=MessageRole.USER)
        assert message.id is None
        assert message.created_at is not None
        assert message.updated_at is not None

    def test_content_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="content"):
            Message(
                conversation_id=1,
                role=MessageRole.USER,
                content="A" * 100001,
            )

    def test_negative_token_count_raises(self) -> None:
        with pytest.raises(ValidationError, match="token_count"):
            Message(
                conversation_id=1,
                role=MessageRole.USER,
                token_count=-1,
            )

    def test_user_role_message(self) -> None:
        message = Message(conversation_id=1, role=MessageRole.USER, content="你好")
        assert message.role == MessageRole.USER

    def test_assistant_role_message(self) -> None:
        message = Message(
            conversation_id=1, role=MessageRole.ASSISTANT, content="你好",
        )
        assert message.role == MessageRole.ASSISTANT
