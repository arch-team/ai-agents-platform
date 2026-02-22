"""ConversationRepositoryImpl 单元测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.repositories.conversation_repository import (
    IConversationRepository,
)
from src.modules.execution.domain.value_objects.conversation_status import ConversationStatus
from src.modules.execution.infrastructure.persistence.models.conversation_model import (
    ConversationModel,
)
from src.modules.execution.infrastructure.persistence.repositories.conversation_repository_impl import (
    ConversationRepositoryImpl,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


@pytest.mark.unit
class TestConversationRepositoryImplStructure:
    def test_implements_iconversation_repository(self) -> None:
        assert issubclass(ConversationRepositoryImpl, IConversationRepository)

    def test_extends_pydantic_repository(self) -> None:
        assert issubclass(ConversationRepositoryImpl, PydanticRepository)

    def test_entity_class_is_conversation(self) -> None:
        assert ConversationRepositoryImpl.entity_class is Conversation

    def test_model_class_is_conversation_model(self) -> None:
        assert ConversationRepositoryImpl.model_class is ConversationModel

    def test_updatable_fields_defined(self) -> None:
        expected = frozenset({"title", "status", "message_count", "total_tokens"})
        assert ConversationRepositoryImpl._updatable_fields == expected


@pytest.mark.unit
class TestConversationRepositoryImplToEntity:
    def test_to_entity_converts_model(self) -> None:
        now = datetime.now(UTC)
        model = ConversationModel(
            id=1,
            title="测试对话",
            agent_id=10,
            user_id=42,
            status="active",
            message_count=5,
            total_tokens=100,
            created_at=now,
            updated_at=now,
        )
        repo = ConversationRepositoryImpl.__new__(ConversationRepositoryImpl)
        entity = repo._to_entity(model)

        assert isinstance(entity, Conversation)
        assert entity.id == 1
        assert entity.title == "测试对话"
        assert entity.agent_id == 10
        assert entity.user_id == 42
        assert entity.status == ConversationStatus.ACTIVE
        assert entity.message_count == 5
        assert entity.total_tokens == 100

    def test_to_entity_converts_completed_status(self) -> None:
        now = datetime.now(UTC)
        model = ConversationModel(
            id=2,
            title="已完成对话",
            agent_id=10,
            user_id=42,
            status="completed",
            message_count=10,
            total_tokens=200,
            created_at=now,
            updated_at=now,
        )
        repo = ConversationRepositoryImpl.__new__(ConversationRepositoryImpl)
        entity = repo._to_entity(model)

        assert entity.status == ConversationStatus.COMPLETED


@pytest.mark.unit
class TestConversationRepositoryImplToModel:
    def test_to_model_converts_entity(self) -> None:
        conversation = Conversation(
            id=1,
            title="测试对话",
            agent_id=10,
            user_id=42,
            status=ConversationStatus.ACTIVE,
            message_count=5,
            total_tokens=100,
        )
        repo = ConversationRepositoryImpl.__new__(ConversationRepositoryImpl)
        model = repo._to_model(conversation)

        assert isinstance(model, ConversationModel)
        assert model.title == "测试对话"
        assert model.agent_id == 10
        assert model.user_id == 42
        assert model.status == "active"
        assert model.message_count == 5
        assert model.total_tokens == 100

    def test_to_model_converts_failed_status(self) -> None:
        conversation = Conversation(
            id=2,
            title="失败对话",
            agent_id=10,
            user_id=42,
            status=ConversationStatus.FAILED,
        )
        repo = ConversationRepositoryImpl.__new__(ConversationRepositoryImpl)
        model = repo._to_model(conversation)

        assert model.status == "failed"


@pytest.mark.unit
class TestConversationRepositoryImplGetUpdateData:
    def test_get_update_data_returns_updatable_fields(self) -> None:
        conversation = Conversation(
            id=1,
            title="新标题",
            agent_id=10,
            user_id=42,
            status=ConversationStatus.COMPLETED,
            message_count=10,
            total_tokens=200,
        )
        repo = ConversationRepositoryImpl.__new__(ConversationRepositoryImpl)
        data = repo._get_update_data(conversation)

        assert data["title"] == "新标题"
        assert data["status"] == "completed"
        assert data["message_count"] == 10
        assert data["total_tokens"] == 200

    def test_get_update_data_excludes_non_updatable_fields(self) -> None:
        conversation = Conversation(
            id=1,
            title="标题",
            agent_id=10,
            user_id=42,
        )
        repo = ConversationRepositoryImpl.__new__(ConversationRepositoryImpl)
        data = repo._get_update_data(conversation)

        assert "agent_id" not in data
        assert "user_id" not in data
        assert "id" not in data
        assert "created_at" not in data
        assert "updated_at" not in data


@pytest.mark.unit
class TestConversationRepositoryImplQueryMethods:
    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session: AsyncMock) -> ConversationRepositoryImpl:
        return ConversationRepositoryImpl(session=mock_session)

    @pytest.mark.asyncio
    async def test_list_by_user_returns_empty_list(
        self, repo: ConversationRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repo.list_by_user(user_id=42)
        assert result == []

    @pytest.mark.asyncio
    async def test_count_by_user_returns_count(
        self, repo: ConversationRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result

        result = await repo.count_by_user(user_id=42)
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_by_user_with_agent_id_returns_count(
        self, repo: ConversationRepositoryImpl, mock_session: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        mock_session.execute.return_value = mock_result

        result = await repo.count_by_user(user_id=42, agent_id=10)
        assert result == 3
