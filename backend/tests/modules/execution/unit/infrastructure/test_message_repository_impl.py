"""MessageRepositoryImpl 单元测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.execution.domain.entities.message import Message
from src.modules.execution.domain.repositories.message_repository import IMessageRepository
from src.modules.execution.domain.value_objects.message_role import MessageRole
from src.modules.execution.infrastructure.persistence.models.message_model import MessageModel
from src.modules.execution.infrastructure.persistence.repositories.message_repository_impl import (
    MessageRepositoryImpl,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


@pytest.mark.unit
class TestMessageRepositoryImplStructure:
    def test_implements_imessage_repository(self) -> None:
        assert issubclass(MessageRepositoryImpl, IMessageRepository)

    def test_extends_pydantic_repository(self) -> None:
        assert issubclass(MessageRepositoryImpl, PydanticRepository)

    def test_entity_class_is_message(self) -> None:
        assert MessageRepositoryImpl.entity_class is Message

    def test_model_class_is_message_model(self) -> None:
        assert MessageRepositoryImpl.model_class is MessageModel

    def test_updatable_fields_defined(self) -> None:
        expected = frozenset({"content", "token_count"})
        assert MessageRepositoryImpl._updatable_fields == expected


@pytest.mark.unit
class TestMessageRepositoryImplToEntity:
    def test_to_entity_converts_model(self) -> None:
        now = datetime.now(UTC)
        model = MessageModel(
            id=1,
            conversation_id=10,
            role="user",
            content="你好",
            token_count=5,
            created_at=now,
            updated_at=now,
        )
        repo = MessageRepositoryImpl.__new__(MessageRepositoryImpl)
        entity = repo._to_entity(model)

        assert isinstance(entity, Message)
        assert entity.id == 1
        assert entity.conversation_id == 10
        assert entity.role == MessageRole.USER
        assert entity.content == "你好"
        assert entity.token_count == 5

    def test_to_entity_converts_assistant_role(self) -> None:
        now = datetime.now(UTC)
        model = MessageModel(
            id=2,
            conversation_id=10,
            role="assistant",
            content="你好！",
            token_count=10,
            created_at=now,
            updated_at=now,
        )
        repo = MessageRepositoryImpl.__new__(MessageRepositoryImpl)
        entity = repo._to_entity(model)

        assert entity.role == MessageRole.ASSISTANT


@pytest.mark.unit
class TestMessageRepositoryImplToModel:
    def test_to_model_converts_entity(self) -> None:
        message = Message(
            id=1,
            conversation_id=10,
            role=MessageRole.USER,
            content="你好",
            token_count=5,
        )
        repo = MessageRepositoryImpl.__new__(MessageRepositoryImpl)
        model = repo._to_model(message)

        assert isinstance(model, MessageModel)
        assert model.conversation_id == 10
        assert model.role == "user"
        assert model.content == "你好"
        assert model.token_count == 5

    def test_to_model_converts_assistant_role(self) -> None:
        message = Message(
            id=2,
            conversation_id=10,
            role=MessageRole.ASSISTANT,
            content="你好！",
            token_count=10,
        )
        repo = MessageRepositoryImpl.__new__(MessageRepositoryImpl)
        model = repo._to_model(message)

        assert model.role == "assistant"


@pytest.mark.unit
class TestMessageRepositoryImplGetUpdateData:
    def test_get_update_data_returns_updatable_fields(self) -> None:
        message = Message(
            id=1,
            conversation_id=10,
            role=MessageRole.USER,
            content="更新内容",
            token_count=15,
        )
        repo = MessageRepositoryImpl.__new__(MessageRepositoryImpl)
        data = repo._get_update_data(message)

        assert data["content"] == "更新内容"
        assert data["token_count"] == 15

    def test_get_update_data_excludes_non_updatable_fields(self) -> None:
        message = Message(
            id=1,
            conversation_id=10,
            role=MessageRole.USER,
            content="内容",
            token_count=5,
        )
        repo = MessageRepositoryImpl.__new__(MessageRepositoryImpl)
        data = repo._get_update_data(message)

        assert "conversation_id" not in data
        assert "role" not in data
        assert "id" not in data
        assert "created_at" not in data
        assert "updated_at" not in data


@pytest.mark.unit
class TestMessageRepositoryImplQueryMethods:
    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session: AsyncMock) -> MessageRepositoryImpl:
        return MessageRepositoryImpl(session=mock_session)

    @pytest.mark.asyncio
    async def test_list_by_conversation_returns_empty_list(
        self, repo: MessageRepositoryImpl, mock_session: AsyncMock
    ) -> None:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repo.list_by_conversation(conversation_id=10)
        assert result == []

    @pytest.mark.asyncio
    async def test_count_by_conversation_returns_count(
        self, repo: MessageRepositoryImpl, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 8
        mock_session.execute.return_value = mock_result

        result = await repo.count_by_conversation(conversation_id=10)
        assert result == 8
