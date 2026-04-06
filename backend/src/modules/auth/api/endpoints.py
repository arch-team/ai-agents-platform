"""Auth API 端点。"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request, Response, status

from src.modules.auth.api.dependencies import get_current_user, get_user_service
from src.modules.auth.api.schemas.requests import LoginRequest, LogoutRequest, RefreshTokenRequest, RegisterRequest
from src.modules.auth.api.schemas.responses import MessageResponse, TokenResponse, UserResponse
from src.modules.auth.application.dto.user_dto import CreateUserDTO, LoginDTO, RefreshTokenDTO, UserDTO
from src.modules.auth.application.services.user_service import UserService
from src.modules.auth.domain.exceptions import RegistrationDisabledError
from src.shared.api.middleware.rate_limit import rate_limit
from src.shared.infrastructure.settings import Settings, get_settings


# Cookie 名称常量
_ACCESS_TOKEN_COOKIE = "access_token"
_REFRESH_TOKEN_COOKIE = "refresh_token"

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _bind_client_context(request: Request) -> None:
    """将客户端 IP 和 User-Agent 绑定到 structlog 上下文。"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    structlog.contextvars.bind_contextvars(
        client_ip=client_ip,
        user_agent=user_agent,
    )


def _user_response(user: UserDTO) -> UserResponse:
    """将 UserDTO 转换为 API 响应模型。"""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
    )


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, settings: Settings) -> None:
    """在 Response 上设置 httpOnly Cookie，使前端刷新页面后仍保持登录。"""
    response.set_cookie(
        key=_ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,
        secure=settings.ENV_NAME != "dev",
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            key=_REFRESH_TOKEN_COOKIE,
            value=refresh_token,
            httponly=True,
            secure=settings.ENV_NAME != "dev",
            samesite="lax",
            max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/api/v1/auth",
        )


def _clear_auth_cookies(response: Response) -> None:
    """清除认证 Cookie。"""
    response.delete_cookie(key=_ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(key=_REFRESH_TOKEN_COOKIE, path="/api/v1/auth")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@rate_limit("3/hour")
async def register(
    request: Request,
    body: RegisterRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserResponse:
    """注册新用户。REGISTRATION_ENABLED=False 时抛出 RegistrationDisabledError (403)。"""
    _bind_client_context(request)
    if not settings.REGISTRATION_ENABLED:
        raise RegistrationDisabledError
    dto = CreateUserDTO(email=body.email, password=body.password, name=body.name)
    user = await service.register(dto)
    return _user_response(user)


@router.post("/login")
@rate_limit("5/minute")
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """用户登录，返回 JWT token + refresh token，同时设置 httpOnly Cookie。"""
    _bind_client_context(request)
    dto = LoginDTO(email=body.email, password=body.password)
    token = await service.login(dto)
    _set_auth_cookies(response, token.access_token, token.refresh_token, settings)
    return TokenResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
    )


@router.post("/refresh")
@rate_limit("10/minute")
async def refresh_token(
    request: Request,
    response: Response,
    body: RefreshTokenRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """使用 Refresh Token 换发新的 Access Token，同时刷新 httpOnly Cookie。"""
    _bind_client_context(request)
    dto = RefreshTokenDTO(refresh_token=body.refresh_token)
    token = await service.refresh_access_token(dto)
    _set_auth_cookies(response, token.access_token, token.refresh_token, settings)
    return TokenResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    body: LogoutRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponse:
    """撤销 Refresh Token（登出），同时清除 httpOnly Cookie。"""
    _bind_client_context(request)
    await service.logout(body.refresh_token)
    _clear_auth_cookies(response)
    return MessageResponse(message="已成功登出")


@router.get("/me")
async def get_me(
    current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> UserResponse:
    """获取当前登录用户信息。"""
    return _user_response(current_user)
