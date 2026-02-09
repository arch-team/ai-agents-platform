"""Auth API dependencies for FastAPI DI."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.auth.application.services.token_service import decode_access_token
from src.modules.auth.application.services.user_service import UserService
from src.modules.auth.domain.exceptions import AuthenticationError, AuthorizationError
from src.modules.auth.domain.value_objects.role import Role
from src.modules.auth.infrastructure.persistence.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from src.shared.infrastructure.database import get_db
from src.shared.infrastructure.settings import Settings, get_settings


security = HTTPBearer()


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserService:
    """FastAPI 依赖: 创建 UserService 实例。"""
    repository = UserRepositoryImpl(session=session)
    return UserService(
        repository,
        jwt_secret_key=settings.JWT_SECRET_KEY.get_secret_value(),
        jwt_algorithm=settings.JWT_ALGORITHM,
        jwt_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserDTO:
    """FastAPI 依赖: 从 JWT token 解析当前用户。

    Raises:
        AuthenticationError: token 无效或用户不存在
    """
    payload = decode_access_token(
        credentials.credentials,
        secret_key=settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    user_id_str = payload.get("sub")
    if user_id_str is None:
        msg = "无效的认证令牌"
        raise AuthenticationError(msg)

    repository = UserRepositoryImpl(session=session)
    service = UserService(
        repository,
        jwt_secret_key=settings.JWT_SECRET_KEY.get_secret_value(),
        jwt_algorithm=settings.JWT_ALGORITHM,
        jwt_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    user = await service.get_user(int(str(user_id_str)))
    if user is None:
        msg = "用户不存在"
        raise AuthenticationError(msg)
    return user


def require_role(*roles: Role) -> Callable[..., Awaitable[UserDTO]]:
    """FastAPI 依赖工厂: 验证用户角色。

    Raises:
        AuthorizationError: 用户角色不在允许列表中
    """

    async def _check_role(
        current_user: Annotated[UserDTO, Depends(get_current_user)],
    ) -> UserDTO:
        if current_user.role not in {r.value for r in roles}:
            raise AuthorizationError
        return current_user

    return _check_role
