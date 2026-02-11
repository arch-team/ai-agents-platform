"""auth application 层测试共享工具。"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

from src.modules.auth.application.services.user_service import UserService
from src.modules.auth.domain.entities.refresh_token import RefreshToken
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.role import Role

# 测试用 JWT 配置
JWT_SECRET = "test-secret-key-minimum-32bytes-long!"  # noqa: S105
JWT_ALGORITHM = "HS256"
JWT_EXPIRE = 30
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 30
LOG_MODULE = "src.modules.auth.application.services.user_service"


def make_service(
    mock_user_repo: AsyncMock,
    *,
    mock_rt_repo: AsyncMock | None = None,
    max_login_attempts: int = MAX_LOGIN_ATTEMPTS,
    lockout_minutes: int = LOCKOUT_MINUTES,
) -> UserService:
    """创建测试用 UserService 实例。"""
    return UserService(
        mock_user_repo,
        jwt_secret_key=JWT_SECRET,
        jwt_algorithm=JWT_ALGORITHM,
        jwt_expire_minutes=JWT_EXPIRE,
        max_login_attempts=max_login_attempts,
        lockout_minutes=lockout_minutes,
        refresh_token_repository=mock_rt_repo,
    )


def make_user(
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
    """创建测试用 User 实体。"""
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


def make_refresh_token(
    *,
    token: str = "valid-refresh-token",
    user_id: int = 1,
    revoked: bool = False,
    expired: bool = False,
) -> RefreshToken:
    """创建测试用 RefreshToken 实体。"""
    expires_at = datetime.now(UTC) + (timedelta(days=-1) if expired else timedelta(days=7))
    return RefreshToken(
        id=1,
        token=token,
        user_id=user_id,
        revoked=revoked,
        expires_at=expires_at,
    )
