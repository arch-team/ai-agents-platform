"""UserService 测试。"""

import pytest
from unittest.mock import AsyncMock

from src.modules.auth.application.dto.user_dto import CreateUserDTO, LoginDTO
from src.modules.auth.application.services.password_service import hash_password
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
)
from src.modules.auth.domain.repositories.user_repository import IUserRepository

from .conftest import make_service, make_user


@pytest.mark.unit
class TestUserServiceRegister:
    @pytest.mark.asyncio
    async def test_register_creates_user(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None
        mock_repo.create.side_effect = lambda u: make_user(email=u.email, name=u.name)

        service = make_service(mock_repo)
        dto = CreateUserDTO(email="new@example.com", password="password123", name="New User")
        result = await service.register(dto)

        assert result.email == "new@example.com"
        assert result.name == "New User"
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_raises_if_email_exists(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = make_user()

        service = make_service(mock_repo)
        dto = CreateUserDTO(email="test@example.com", password="pw", name="Dup")

        with pytest.raises(UserAlreadyExistsError):
            await service.register(dto)

    @pytest.mark.asyncio
    async def test_register_hashes_password(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None
        created_user = None

        async def capture_create(user: User) -> User:
            nonlocal created_user
            created_user = user
            return make_user(email=user.email, name=user.name)

        mock_repo.create.side_effect = capture_create
        service = make_service(mock_repo)
        await service.register(CreateUserDTO(email="a@b.com", password="plain", name="A"))

        assert created_user is not None
        assert created_user.hashed_password != "plain"
        assert created_user.hashed_password.startswith("$2b$")


@pytest.mark.unit
class TestUserServiceLogin:
    @pytest.mark.asyncio
    async def test_login_returns_token(self) -> None:
        hashed = hash_password("correct-password")
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = make_user(password=hashed)

        service = make_service(mock_repo)
        result = await service.login(LoginDTO(email="test@example.com", password="correct-password"))

        assert result.access_token is not None
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_email_raises(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None

        service = make_service(mock_repo)
        with pytest.raises(AuthenticationError, match="邮箱或密码错误"):
            await service.login(LoginDTO(email="nobody@test.com", password="pw"))

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self) -> None:
        hashed = hash_password("correct-password")
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = make_user(password=hashed)

        service = make_service(mock_repo)
        with pytest.raises(AuthenticationError, match="邮箱或密码错误"):
            await service.login(LoginDTO(email="test@example.com", password="wrong"))

    @pytest.mark.asyncio
    async def test_login_inactive_user_raises(self) -> None:
        hashed = hash_password("password")
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = make_user(password=hashed, is_active=False)

        service = make_service(mock_repo)
        with pytest.raises(AuthenticationError, match="账户已停用"):
            await service.login(LoginDTO(email="test@example.com", password="password"))


@pytest.mark.unit
class TestUserServiceGetUser:
    @pytest.mark.asyncio
    async def test_get_user_returns_dto(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_id.return_value = make_user()

        service = make_service(mock_repo)
        result = await service.get_user(1)

        assert result is not None
        assert result.id == 1
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_returns_none_for_missing(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_id.return_value = None

        service = make_service(mock_repo)
        result = await service.get_user(9999)
        assert result is None
