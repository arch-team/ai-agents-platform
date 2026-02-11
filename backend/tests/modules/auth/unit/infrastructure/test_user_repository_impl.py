"""UserRepositoryImpl 单元测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.modules.auth.domain.value_objects.role import Role
from src.modules.auth.infrastructure.persistence.models.user_model import UserModel
from src.modules.auth.infrastructure.persistence.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


@pytest.mark.unit
class TestUserRepositoryImplStructure:
    def test_implements_iuser_repository(self) -> None:
        assert issubclass(UserRepositoryImpl, IUserRepository)

    def test_extends_pydantic_repository(self) -> None:
        assert issubclass(UserRepositoryImpl, PydanticRepository)

    def test_entity_class_is_user(self) -> None:
        assert UserRepositoryImpl.entity_class is User

    def test_model_class_is_user_model(self) -> None:
        assert UserRepositoryImpl.model_class is UserModel

    def test_updatable_fields_defined(self) -> None:
        expected = frozenset({"name", "role", "is_active", "hashed_password", "failed_login_count", "locked_until", "updated_at"})
        assert UserRepositoryImpl._updatable_fields == expected


@pytest.mark.unit
class TestUserRepositoryImplEntityModelConversion:
    def test_to_model_converts_user_entity(self) -> None:
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed123",
            name="Test User",
            role=Role.VIEWER,
        )
        repo = UserRepositoryImpl.__new__(UserRepositoryImpl)
        model = repo._to_model(user)
        assert isinstance(model, UserModel)
        assert model.email == "test@example.com"
        assert model.name == "Test User"
        assert model.role == "viewer"

    def test_to_entity_converts_user_model(self) -> None:
        now = datetime.now(UTC)
        model = UserModel(
            id=1,
            email="test@example.com",
            hashed_password="hashed123",
            name="Test User",
            role="viewer",
            is_active=True,
            failed_login_count=0,
            locked_until=None,
            created_at=now,
            updated_at=now,
        )
        repo = UserRepositoryImpl.__new__(UserRepositoryImpl)
        entity = repo._to_entity(model)
        assert isinstance(entity, User)
        assert entity.email == "test@example.com"
        assert entity.role == Role.VIEWER


@pytest.mark.unit
class TestUserRepositoryImplGetByEmail:
    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session: AsyncMock) -> UserRepositoryImpl:
        return UserRepositoryImpl(session=mock_session)

    @pytest.mark.asyncio
    async def test_get_by_email_returns_none_when_not_found(
        self, repo: UserRepositoryImpl, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_email("notfound@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email_returns_user_when_found(
        self, repo: UserRepositoryImpl, mock_session: AsyncMock
    ) -> None:
        now = datetime.now(UTC)
        mock_model = UserModel(
            id=1,
            email="found@example.com",
            hashed_password="hashed",
            name="Found User",
            role="developer",
            is_active=True,
            failed_login_count=0,
            locked_until=None,
            created_at=now,
            updated_at=now,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_email("found@example.com")
        assert result is not None
        assert result.email == "found@example.com"
        assert result.role == Role.DEVELOPER
