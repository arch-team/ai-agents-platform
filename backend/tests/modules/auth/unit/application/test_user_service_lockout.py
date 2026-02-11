"""UserService 账户锁定逻辑单元测试。"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.modules.auth.application.dto.user_dto import LoginDTO
from src.modules.auth.application.services.password_service import hash_password
from src.modules.auth.application.services.user_service import UserService
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.exceptions import AccountLockedError, AuthenticationError
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.modules.auth.domain.value_objects.role import Role


# 测试用配置
_JWT_SECRET = "test-secret-key"
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE = 30
_MAX_LOGIN_ATTEMPTS = 5
_LOCKOUT_MINUTES = 30


def _make_service(mock_repo: AsyncMock) -> UserService:
    return UserService(
        mock_repo,
        jwt_secret_key=_JWT_SECRET,
        jwt_algorithm=_JWT_ALGORITHM,
        jwt_expire_minutes=_JWT_EXPIRE,
        max_login_attempts=_MAX_LOGIN_ATTEMPTS,
        lockout_minutes=_LOCKOUT_MINUTES,
    )


def _make_user(
    *,
    user_id: int = 1,
    email: str = "test@example.com",
    password: str = "hashed",
    name: str = "Test User",
    role: Role = Role.VIEWER,
    is_active: bool = True,
    failed_login_count: int = 0,
    locked_until: datetime | None = None,
) -> User:
    return User(
        id=user_id,
        email=email,
        hashed_password=password,
        name=name,
        role=role,
        is_active=is_active,
        failed_login_count=failed_login_count,
        locked_until=locked_until,
    )


@pytest.mark.unit
class TestUserServiceLoginLockout:
    """UserService 登录锁定逻辑测试。"""

    @pytest.mark.asyncio
    async def test_login_locked_account_raises_account_locked(self) -> None:
        """锁定期间登录应抛出 AccountLockedError。"""
        locked_user = _make_user(
            password=hash_password("correct"),
            failed_login_count=5,
            locked_until=datetime.now(UTC) + timedelta(minutes=25),
        )
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = locked_user

        service = _make_service(mock_repo)
        with pytest.raises(AccountLockedError):
            await service.login(
                LoginDTO(email="test@example.com", password="correct"),
            )

    @pytest.mark.asyncio
    async def test_login_locked_account_with_correct_password_still_raises(self) -> None:
        """锁定期间即使密码正确也应拒绝登录。"""
        locked_user = _make_user(
            password=hash_password("correct"),
            failed_login_count=5,
            locked_until=datetime.now(UTC) + timedelta(minutes=25),
        )
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = locked_user

        service = _make_service(mock_repo)
        with pytest.raises(AccountLockedError):
            await service.login(
                LoginDTO(email="test@example.com", password="correct"),
            )

    @pytest.mark.asyncio
    async def test_wrong_password_increments_failed_count(self) -> None:
        """错误密码应递增失败计数并持久化。"""
        hashed = hash_password("correct")
        user = _make_user(password=hashed, failed_login_count=0)
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = user

        service = _make_service(mock_repo)
        with pytest.raises(AuthenticationError):
            await service.login(
                LoginDTO(email="test@example.com", password="wrong"),
            )

        # 验证 update 被调用以持久化失败计数
        mock_repo.update.assert_called_once()
        updated_user = mock_repo.update.call_args[0][0]
        assert updated_user.failed_login_count == 1

    @pytest.mark.asyncio
    async def test_fifth_wrong_password_locks_account(self) -> None:
        """第 5 次错误密码应锁定账户。"""
        hashed = hash_password("correct")
        user = _make_user(password=hashed, failed_login_count=4)
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = user

        service = _make_service(mock_repo)
        with pytest.raises(AuthenticationError):
            await service.login(
                LoginDTO(email="test@example.com", password="wrong"),
            )

        mock_repo.update.assert_called_once()
        updated_user = mock_repo.update.call_args[0][0]
        assert updated_user.failed_login_count == 5
        assert updated_user.locked_until is not None

    @pytest.mark.asyncio
    async def test_successful_login_resets_failed_count(self) -> None:
        """成功登录应重置失败计数。"""
        hashed = hash_password("correct")
        user = _make_user(password=hashed, failed_login_count=3)
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = user

        service = _make_service(mock_repo)
        result = await service.login(
            LoginDTO(email="test@example.com", password="correct"),
        )

        assert result.access_token is not None
        mock_repo.update.assert_called_once()
        updated_user = mock_repo.update.call_args[0][0]
        assert updated_user.failed_login_count == 0
        assert updated_user.locked_until is None

    @pytest.mark.asyncio
    async def test_login_after_lockout_expires_succeeds(self) -> None:
        """锁定过期后应可正常登录。"""
        hashed = hash_password("correct")
        user = _make_user(
            password=hashed,
            failed_login_count=5,
            locked_until=datetime.now(UTC) - timedelta(minutes=1),
        )
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = user

        service = _make_service(mock_repo)
        result = await service.login(
            LoginDTO(email="test@example.com", password="correct"),
        )

        assert result.access_token is not None
        # 应重置失败计数
        mock_repo.update.assert_called_once()
        updated_user = mock_repo.update.call_args[0][0]
        assert updated_user.failed_login_count == 0

    @pytest.mark.asyncio
    async def test_login_wrong_email_does_not_reveal_user_existence(self) -> None:
        """错误邮箱应返回通用错误，不暴露用户是否存在。"""
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None

        service = _make_service(mock_repo)
        with pytest.raises(AuthenticationError, match="邮箱或密码错误"):
            await service.login(
                LoginDTO(email="nobody@example.com", password="pw"),
            )
        # 不应调用 update（因为用户不存在）
        mock_repo.update.assert_not_called()
