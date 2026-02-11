"""UserService Refresh Token 相关测试。"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.modules.auth.application.dto.user_dto import LoginDTO, RefreshTokenDTO
from src.modules.auth.application.services.password_service import hash_password
from src.modules.auth.application.services.user_service import UserService
from src.modules.auth.domain.entities.refresh_token import RefreshToken
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.exceptions import (
    AuthenticationError,
    InvalidRefreshTokenError,
)
from src.modules.auth.domain.repositories.refresh_token_repository import (
    IRefreshTokenRepository,
)
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.modules.auth.domain.value_objects.role import Role

# 测试用 JWT 配置
_JWT_SECRET = "test-secret-key"  # noqa: S105
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE = 30


def _make_service(
    mock_user_repo: AsyncMock,
    mock_rt_repo: AsyncMock | None = None,
) -> UserService:
    return UserService(
        mock_user_repo,
        jwt_secret_key=_JWT_SECRET,
        jwt_algorithm=_JWT_ALGORITHM,
        jwt_expire_minutes=_JWT_EXPIRE,
        refresh_token_repository=mock_rt_repo,
    )


def _make_user(
    *,
    user_id: int = 1,
    email: str = "test@example.com",
    password: str = "hashed",
    name: str = "Test User",
    role: Role = Role.VIEWER,
    is_active: bool = True,
) -> User:
    return User(
        id=user_id,
        email=email,
        hashed_password=password,
        name=name,
        role=role,
        is_active=is_active,
    )


def _make_refresh_token(
    *,
    token: str = "valid-refresh-token",
    user_id: int = 1,
    revoked: bool = False,
    expired: bool = False,
) -> RefreshToken:
    expires_at = datetime.now(UTC) + (timedelta(days=-1) if expired else timedelta(days=7))
    return RefreshToken(
        id=1,
        token=token,
        user_id=user_id,
        revoked=revoked,
        expires_at=expires_at,
    )


@pytest.mark.unit
class TestLoginWithRefreshToken:
    @pytest.mark.asyncio
    async def test_login_returns_refresh_token(self) -> None:
        """登录成功时返回 refresh_token。"""
        hashed = hash_password("correct-password")
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_email.return_value = _make_user(password=hashed)

        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        rt = _make_refresh_token(token="new-rt-token")
        mock_rt_repo.create.return_value = rt

        service = _make_service(mock_user_repo, mock_rt_repo)
        result = await service.login(LoginDTO(email="test@example.com", password="correct-password"))

        assert result.access_token != ""
        assert result.refresh_token == "new-rt-token"
        mock_rt_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_without_rt_repo_returns_empty_refresh_token(self) -> None:
        """未配置 refresh_token_repository 时，refresh_token 为空。"""
        hashed = hash_password("correct-password")
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_email.return_value = _make_user(password=hashed)

        service = _make_service(mock_user_repo, None)
        result = await service.login(LoginDTO(email="test@example.com", password="correct-password"))

        assert result.access_token != ""
        assert result.refresh_token == ""


@pytest.mark.unit
class TestRefreshAccessToken:
    @pytest.mark.asyncio
    async def test_refresh_returns_new_access_token(self) -> None:
        """有效 refresh_token 可以换发新的 access_token。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_id.return_value = _make_user()

        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = _make_refresh_token()

        service = _make_service(mock_user_repo, mock_rt_repo)
        result = await service.refresh_access_token(
            RefreshTokenDTO(refresh_token="valid-refresh-token"),
        )

        assert result.access_token != ""
        assert result.refresh_token == "valid-refresh-token"

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token_raises(self) -> None:
        """无效 refresh_token 抛出 InvalidRefreshTokenError。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = None

        service = _make_service(mock_user_repo, mock_rt_repo)
        with pytest.raises(InvalidRefreshTokenError):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="invalid-token"),
            )

    @pytest.mark.asyncio
    async def test_refresh_with_revoked_token_raises(self) -> None:
        """已撤销的 refresh_token 抛出 InvalidRefreshTokenError。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = _make_refresh_token(revoked=True)

        service = _make_service(mock_user_repo, mock_rt_repo)
        with pytest.raises(InvalidRefreshTokenError):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="valid-refresh-token"),
            )

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token_raises(self) -> None:
        """已过期的 refresh_token 抛出 InvalidRefreshTokenError。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = _make_refresh_token(expired=True)

        service = _make_service(mock_user_repo, mock_rt_repo)
        with pytest.raises(InvalidRefreshTokenError):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="valid-refresh-token"),
            )

    @pytest.mark.asyncio
    async def test_refresh_with_inactive_user_raises(self) -> None:
        """用户停用后 refresh 返回 401。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_id.return_value = _make_user(is_active=False)

        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = _make_refresh_token()

        service = _make_service(mock_user_repo, mock_rt_repo)
        with pytest.raises(AuthenticationError, match="账户已停用"):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="valid-refresh-token"),
            )
        # 验证 Token 被撤销
        mock_rt_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_with_nonexistent_user_raises(self) -> None:
        """用户不存在时 refresh 抛出 AuthenticationError。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_id.return_value = None

        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = _make_refresh_token()

        service = _make_service(mock_user_repo, mock_rt_repo)
        with pytest.raises(AuthenticationError, match="账户已停用"):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="valid-refresh-token"),
            )

    @pytest.mark.asyncio
    async def test_refresh_without_rt_repo_raises(self) -> None:
        """未配置 refresh_token_repository 时抛出 InvalidRefreshTokenError。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        service = _make_service(mock_user_repo, None)
        with pytest.raises(InvalidRefreshTokenError, match="未启用"):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="any-token"),
            )


@pytest.mark.unit
class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_revokes_token(self) -> None:
        """登出撤销 refresh_token。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.revoke_by_token.return_value = True

        service = _make_service(mock_user_repo, mock_rt_repo)
        result = await service.logout("some-token")

        assert result is True
        mock_rt_repo.revoke_by_token.assert_called_once_with("some-token")

    @pytest.mark.asyncio
    async def test_logout_without_rt_repo_returns_false(self) -> None:
        """未配置 refresh_token_repository 时返回 False。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        service = _make_service(mock_user_repo, None)
        result = await service.logout("some-token")
        assert result is False


@pytest.mark.unit
class TestRevokeUserTokens:
    @pytest.mark.asyncio
    async def test_revoke_user_tokens(self) -> None:
        """撤销用户所有 refresh token。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.revoke_by_user_id.return_value = 3

        service = _make_service(mock_user_repo, mock_rt_repo)
        result = await service.revoke_user_tokens(1)

        assert result == 3
        mock_rt_repo.revoke_by_user_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_revoke_user_tokens_without_rt_repo_returns_zero(self) -> None:
        """未配置 refresh_token_repository 时返回 0。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        service = _make_service(mock_user_repo, None)
        result = await service.revoke_user_tokens(1)
        assert result == 0
