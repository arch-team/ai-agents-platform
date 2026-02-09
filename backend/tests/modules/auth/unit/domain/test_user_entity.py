"""User 实体单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.role import Role


@pytest.mark.unit
class TestUserCreation:
    def test_create_user_with_defaults(self) -> None:
        user = User(
            email="test@example.com",
            hashed_password="hashed123",
            name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed123"
        assert user.name == "Test User"
        assert user.role == Role.VIEWER
        assert user.is_active is True

    def test_create_user_with_custom_role(self) -> None:
        user = User(
            email="admin@example.com",
            hashed_password="hashed123",
            name="Admin",
            role=Role.ADMIN,
        )
        assert user.role == Role.ADMIN

    def test_create_user_inherits_pydantic_entity(self) -> None:
        user = User(
            email="test@example.com",
            hashed_password="hashed123",
            name="Test",
        )
        assert user.id is None
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError, match="email"):
            User(
                email="not-an-email",
                hashed_password="hashed123",
                name="Test",
            )

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            User(
                email="test@example.com",
                hashed_password="hashed123",
                name="",
            )

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            User(
                email="test@example.com",
                hashed_password="hashed123",
                name="A" * 101,
            )


@pytest.mark.unit
class TestUserBehavior:
    @pytest.fixture
    def user(self) -> User:
        return User(
            email="test@example.com",
            hashed_password="hashed123",
            name="Test User",
        )

    def test_deactivate(self, user: User) -> None:
        user.deactivate()
        assert user.is_active is False

    def test_activate(self, user: User) -> None:
        user.deactivate()
        user.activate()
        assert user.is_active is True

    def test_change_role(self, user: User) -> None:
        user.change_role(Role.ADMIN)
        assert user.role == Role.ADMIN

    def test_touch_updates_timestamp(self, user: User) -> None:
        original_updated_at = user.updated_at
        user.deactivate()
        assert user.updated_at is not None
        assert original_updated_at is not None
        assert user.updated_at >= original_updated_at
