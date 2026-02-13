"""UserService Refresh Token 相关测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.auth.application.dto.user_dto import LoginDTO, RefreshTokenDTO
from src.modules.auth.application.services.password_service import hash_password
from src.modules.auth.domain.exceptions import (
    AuthenticationError,
    InvalidRefreshTokenError,
)
from src.modules.auth.domain.repositories.refresh_token_repository import (
    IRefreshTokenRepository,
)
from src.modules.auth.domain.repositories.user_repository import IUserRepository

from .conftest import make_refresh_token, make_service, make_user


@pytest.mark.unit
class TestLoginWithRefreshToken:
    @pytest.mark.asyncio
    async def test_login_returns_refresh_token(self) -> None:
        """登录成功时返回 refresh_token。"""
        hashed = hash_password("correct-password")
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_email.return_value = make_user(password=hashed)

        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        rt = make_refresh_token(token="new-rt-token")
        mock_rt_repo.create.return_value = rt

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)
        result = await service.login(LoginDTO(email="test@example.com", password="correct-password"))

        assert result.access_token != ""
        assert result.refresh_token == "new-rt-token"
        mock_rt_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_without_rt_repo_returns_empty_refresh_token(self) -> None:
        """未配置 refresh_token_repository 时，refresh_token 为空。"""
        hashed = hash_password("correct-password")
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_email.return_value = make_user(password=hashed)

        service = make_service(mock_user_repo)
        result = await service.login(LoginDTO(email="test@example.com", password="correct-password"))

        assert result.access_token != ""
        assert result.refresh_token == ""


@pytest.mark.unit
class TestRefreshAccessToken:
    @pytest.mark.asyncio
    async def test_refresh_rotates_token(self) -> None:
        """刷新时撤销旧 Token 并签发新 Token（Token Rotation）。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_id.return_value = make_user()

        old_rt = make_refresh_token(token="old-refresh-token")
        new_rt = make_refresh_token(token="new-refresh-token")

        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = old_rt
        mock_rt_repo.create.return_value = new_rt

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)
        result = await service.refresh_access_token(
            RefreshTokenDTO(refresh_token="old-refresh-token"),
        )

        assert result.access_token != ""
        # 返回的是新 Token, 而非旧 Token
        assert result.refresh_token == "new-refresh-token"
        # 旧 Token 被撤销并更新到数据库
        assert old_rt.revoked is True
        mock_rt_repo.update.assert_called_once_with(old_rt)
        # 新 Token 被创建
        mock_rt_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token_raises(self) -> None:
        """无效 refresh_token 抛出 InvalidRefreshTokenError。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = None

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)
        with pytest.raises(InvalidRefreshTokenError):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="invalid-token"),
            )

    @pytest.mark.asyncio
    async def test_refresh_with_revoked_token_raises(self) -> None:
        """已撤销的 refresh_token 抛出 InvalidRefreshTokenError。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = make_refresh_token(revoked=True)

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)
        with pytest.raises(InvalidRefreshTokenError):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="valid-refresh-token"),
            )

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token_raises(self) -> None:
        """已过期的 refresh_token 抛出 InvalidRefreshTokenError。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = make_refresh_token(expired=True)

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)
        with pytest.raises(InvalidRefreshTokenError):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="valid-refresh-token"),
            )

    @pytest.mark.asyncio
    async def test_refresh_with_inactive_user_raises(self) -> None:
        """用户停用后 refresh 返回 401。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_id.return_value = make_user(is_active=False)

        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = make_refresh_token()

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)
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
        mock_rt_repo.get_by_token.return_value = make_refresh_token()

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)
        with pytest.raises(AuthenticationError, match="账户已停用"):
            await service.refresh_access_token(
                RefreshTokenDTO(refresh_token="valid-refresh-token"),
            )

    @pytest.mark.asyncio
    async def test_refresh_without_rt_repo_raises(self) -> None:
        """未配置 refresh_token_repository 时抛出 InvalidRefreshTokenError。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        service = make_service(mock_user_repo)
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

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)
        result = await service.logout("some-token")

        assert result is True
        mock_rt_repo.revoke_by_token.assert_called_once_with("some-token")

    @pytest.mark.asyncio
    async def test_logout_without_rt_repo_returns_false(self) -> None:
        """未配置 refresh_token_repository 时返回 False。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        service = make_service(mock_user_repo)
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

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)
        result = await service.revoke_user_tokens(1)

        assert result == 3
        mock_rt_repo.revoke_by_user_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_revoke_user_tokens_without_rt_repo_returns_zero(self) -> None:
        """未配置 refresh_token_repository 时返回 0。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        service = make_service(mock_user_repo)
        result = await service.revoke_user_tokens(1)
        assert result == 0
