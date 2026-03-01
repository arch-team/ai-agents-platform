"""安全审计日志测试。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.auth.application.dto.user_dto import CreateUserDTO, LoginDTO, RefreshTokenDTO
from src.modules.auth.application.services.password_service import hash_password
from src.modules.auth.domain.exceptions import (
    AccountLockedError,
    AuthenticationError,
    InvalidRefreshTokenError,
)
from src.modules.auth.domain.repositories.refresh_token_repository import (
    IRefreshTokenRepository,
)
from src.modules.auth.domain.repositories.user_repository import IUserRepository

from .conftest import LOG_MODULE, make_refresh_token, make_service, make_user


@pytest.mark.unit
class TestLoginSecurityAuditLog:
    """登录安全审计日志测试。"""

    @pytest.mark.asyncio
    async def test_login_success_logs_event(self) -> None:
        """登录成功时产生 security_event 日志。"""
        hashed = hash_password("correct-password")
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = make_user(password=hashed)

        service = make_service(mock_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            await service.login(LoginDTO(email="test@example.com", password="correct-password"))

            # 验证登录成功日志
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "security_event"
            assert call_args[1]["event_type"] == "login_success"
            assert call_args[1]["user_id"] == 1

    @pytest.mark.asyncio
    async def test_login_failed_wrong_email_logs_event(self) -> None:
        """邮箱不存在时产生 login_failed 日志。"""
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None

        service = make_service(mock_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            with pytest.raises(AuthenticationError):
                await service.login(LoginDTO(email="no@example.com", password="pw"))

            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args
            assert call_args[0][0] == "security_event"
            assert call_args[1]["event_type"] == "login_failed"
            assert call_args[1]["reason"] == "invalid_credentials"

    @pytest.mark.asyncio
    async def test_login_failed_wrong_password_logs_event(self) -> None:
        """密码错误时产生 login_failed 日志。"""
        hashed = hash_password("correct-password")
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = make_user(password=hashed)

        service = make_service(mock_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            with pytest.raises(AuthenticationError):
                await service.login(LoginDTO(email="test@example.com", password="wrong"))

            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args
            assert call_args[0][0] == "security_event"
            assert call_args[1]["event_type"] == "login_failed"
            assert call_args[1]["reason"] == "invalid_credentials"

    @pytest.mark.asyncio
    async def test_login_inactive_user_logs_event(self) -> None:
        """账户停用时产生 login_failed 日志。"""
        hashed = hash_password("password")
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = make_user(password=hashed, is_active=False)

        service = make_service(mock_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            with pytest.raises(AuthenticationError):
                await service.login(LoginDTO(email="test@example.com", password="password"))

            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args
            assert call_args[1]["event_type"] == "login_failed"
            assert call_args[1]["reason"] == "account_disabled"

    @pytest.mark.asyncio
    async def test_account_locked_logs_event(self) -> None:
        """账户锁定时产生 account_locked 日志。"""
        hashed = hash_password("correct-password")
        user = make_user(password=hashed)
        # 模拟多次失败后锁定
        for _ in range(5):
            user.record_failed_login(max_attempts=5, lockout_minutes=30)

        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = user

        service = make_service(mock_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            with pytest.raises(AccountLockedError):
                await service.login(LoginDTO(email="test@example.com", password="wrong"))

            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args
            assert call_args[1]["event_type"] == "login_failed"
            assert call_args[1]["reason"] == "account_locked"


@pytest.mark.unit
class TestRegisterSecurityAuditLog:
    """注册安全审计日志测试。"""

    @pytest.mark.asyncio
    async def test_register_success_logs_event(self) -> None:
        """注册成功时产生 security_event 日志。"""
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None
        mock_repo.create.side_effect = lambda u: make_user(email=str(u.email), name=u.name)

        service = make_service(mock_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            await service.register(CreateUserDTO(email="new@example.com", password="password123", name="New"))

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "security_event"
            assert call_args[1]["event_type"] == "register_success"


@pytest.mark.unit
class TestTokenSecurityAuditLog:
    """Token 操作安全审计日志测试。"""

    @pytest.mark.asyncio
    async def test_refresh_success_logs_event(self) -> None:
        """Token 刷新成功时产生日志。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_user_repo.get_by_id.return_value = make_user()
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = make_refresh_token()

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            await service.refresh_access_token(RefreshTokenDTO(refresh_token="valid-refresh-token"))

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "security_event"
            assert call_args[1]["event_type"] == "token_refreshed"

    @pytest.mark.asyncio
    async def test_refresh_failed_logs_event(self) -> None:
        """Token 刷新失败时产生日志。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.get_by_token.return_value = None

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            with pytest.raises(InvalidRefreshTokenError):
                await service.refresh_access_token(RefreshTokenDTO(refresh_token="invalid"))

            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args
            assert call_args[1]["event_type"] == "token_refresh_failed"

    @pytest.mark.asyncio
    async def test_logout_logs_event(self) -> None:
        """登出时产生日志。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.revoke_by_token.return_value = True

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            await service.logout("some-token")

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "security_event"
            assert call_args[1]["event_type"] == "logout"

    @pytest.mark.asyncio
    async def test_revoke_user_tokens_logs_event(self) -> None:
        """撤销用户所有 Token 时产生日志。"""
        mock_user_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock(spec=IRefreshTokenRepository)
        mock_rt_repo.revoke_by_user_id.return_value = 2

        service = make_service(mock_user_repo, mock_rt_repo=mock_rt_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            await service.revoke_user_tokens(1)

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert call_args[1]["event_type"] == "tokens_revoked"
            assert call_args[1]["target_user_id"] == 1
            assert call_args[1]["revoked_count"] == 2


@pytest.mark.unit
class TestAuditLogDoesNotLeakSensitiveInfo:
    """验证审计日志不泄露敏感信息。"""

    @pytest.mark.asyncio
    async def test_login_log_does_not_contain_password(self) -> None:
        """登录日志不包含密码信息。"""
        hashed = hash_password("secret-password")
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = make_user(password=hashed)

        service = make_service(mock_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            await service.login(LoginDTO(email="test@example.com", password="secret-password"))

            # 检查所有 info 调用，确保没有密码
            for call in mock_logger.info.call_args_list:
                assert "secret-password" not in str(call)
                assert "password" not in str(call[1])

    @pytest.mark.asyncio
    async def test_register_log_does_not_contain_password(self) -> None:
        """注册日志不包含密码信息。"""
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None
        mock_repo.create.side_effect = lambda u: make_user(email=str(u.email), name=u.name)

        service = make_service(mock_repo)

        with patch(f"{LOG_MODULE}.logger") as mock_logger:
            await service.register(
                CreateUserDTO(email="new@example.com", password="Secret123", name="New"),
            )

            for call in mock_logger.info.call_args_list:
                assert "Secret123" not in str(call)
                assert "password" not in str(call[1])
