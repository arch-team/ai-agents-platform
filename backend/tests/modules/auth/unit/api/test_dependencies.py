"""Auth API dependencies 单元测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import SecretStr

from src.modules.auth.api.dependencies import get_current_user, get_user_service, require_role
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.auth.application.services.token_service import create_access_token
from src.modules.auth.domain.exceptions import AuthenticationError, AuthorizationError
from src.modules.auth.domain.value_objects.role import Role
from src.shared.infrastructure.settings import Settings


# 测试用配置
_JWT_SECRET = "test-secret-key-for-deps-minimum-32bytes!"
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE = 30


def _test_settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY=SecretStr(_JWT_SECRET),
        JWT_ALGORITHM=_JWT_ALGORITHM,
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=_JWT_EXPIRE,
    )


def _make_token(user_id: int = 1, role: str = "viewer") -> str:
    return create_access_token(
        subject=str(user_id),
        secret_key=_JWT_SECRET,
        algorithm=_JWT_ALGORITHM,
        expire_minutes=_JWT_EXPIRE,
        extra_claims={"role": role},
    )


def _make_user_dto(
    user_id: int = 1,
    email: str = "test@example.com",
    name: str = "Test User",
    role: str = "viewer",
    is_active: bool = True,
) -> UserDTO:
    return UserDTO(id=user_id, email=email, name=name, role=role, is_active=is_active)


@pytest.mark.unit
class TestGetUserService:
    def test_returns_user_service_instance(self) -> None:
        mock_session = AsyncMock()
        settings = _test_settings()
        service = get_user_service(session=mock_session, settings=settings)
        assert service is not None
        assert hasattr(service, "register")
        assert hasattr(service, "login")


@pytest.mark.unit
class TestGetCurrentUser:
    def test_is_callable(self) -> None:
        assert callable(get_current_user)

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self) -> None:
        token = _make_token(user_id=42)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        settings = _test_settings()
        expected_user = _make_user_dto(user_id=42)

        mock_service = AsyncMock()
        mock_service.get_user.return_value = expected_user

        result = await get_current_user(
            credentials=credentials, service=mock_service, settings=settings,
        )

        assert result.id == 42
        mock_service.get_user.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_token_without_sub_raises(self) -> None:
        # 创建一个没有 sub 的 token
        import jwt as pyjwt

        token = pyjwt.encode({"role": "admin"}, _JWT_SECRET, algorithm=_JWT_ALGORITHM)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        settings = _test_settings()
        mock_service = AsyncMock()

        with pytest.raises(AuthenticationError, match="无效的认证令牌"):
            await get_current_user(
                credentials=credentials, service=mock_service, settings=settings,
            )

    @pytest.mark.asyncio
    async def test_inactive_user_raises(self) -> None:
        """停用用户持有有效 Token 时应返回 AuthenticationError。"""
        token = _make_token(user_id=10)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        settings = _test_settings()
        inactive_user = _make_user_dto(user_id=10, is_active=False)

        mock_service = AsyncMock()
        mock_service.get_user.return_value = inactive_user

        with pytest.raises(AuthenticationError, match="账户已停用"):
            await get_current_user(
                credentials=credentials, service=mock_service, settings=settings,
            )

    @pytest.mark.asyncio
    async def test_user_not_found_raises(self) -> None:
        token = _make_token(user_id=999)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        settings = _test_settings()

        mock_service = AsyncMock()
        mock_service.get_user.return_value = None

        with pytest.raises(AuthenticationError, match="用户不存在"):
            await get_current_user(
                credentials=credentials, service=mock_service, settings=settings,
            )


@pytest.mark.unit
class TestRequireRole:
    def test_returns_dependency_callable(self) -> None:
        dep = require_role(Role.ADMIN)
        assert callable(dep)

    def test_accepts_multiple_roles(self) -> None:
        dep = require_role(Role.ADMIN, Role.DEVELOPER)
        assert callable(dep)

    @pytest.mark.asyncio
    async def test_matching_role_passes(self) -> None:
        check_fn = require_role(Role.ADMIN, Role.DEVELOPER)
        user = _make_user_dto(role="admin")
        # 直接调用内部函数，绕过 FastAPI DI
        result = await check_fn(current_user=user)
        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_non_matching_role_raises(self) -> None:
        check_fn = require_role(Role.ADMIN)
        user = _make_user_dto(role="viewer")
        with pytest.raises(AuthorizationError):
            await check_fn(current_user=user)
