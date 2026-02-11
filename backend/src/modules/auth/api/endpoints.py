"""Auth API 端点。"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from src.modules.auth.api.dependencies import get_current_user, get_user_service
from src.modules.auth.api.schemas.requests import LoginRequest, LogoutRequest, RefreshTokenRequest, RegisterRequest
from src.modules.auth.api.schemas.responses import MessageResponse, TokenResponse, UserResponse
from src.modules.auth.application.dto.user_dto import CreateUserDTO, LoginDTO, RefreshTokenDTO, UserDTO
from src.modules.auth.application.services.user_service import UserService
from src.shared.api.middleware.rate_limit import limiter
from src.shared.infrastructure.settings import Settings, get_settings


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


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("3/hour")
async def register(
    request: Request,
    body: RegisterRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserResponse | JSONResponse:
    """注册新用户。REGISTRATION_ENABLED=False 时返回 403。"""
    _bind_client_context(request)
    if not settings.REGISTRATION_ENABLED:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"code": "REGISTRATION_DISABLED", "message": "Public registration is disabled", "details": None},
        )
    dto = CreateUserDTO(email=body.email, password=body.password, name=body.name)
    user = await service.register(dto)
    return _user_response(user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    """用户登录，返回 JWT token + refresh token。"""
    _bind_client_context(request)
    dto = LoginDTO(email=body.email, password=body.password)
    token = await service.login(dto)
    return TokenResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    """使用 Refresh Token 换发新的 Access Token。"""
    _bind_client_context(request)
    dto = RefreshTokenDTO(refresh_token=body.refresh_token)
    token = await service.refresh_access_token(dto)
    return TokenResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    body: LogoutRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponse:
    """撤销 Refresh Token（登出）。"""
    _bind_client_context(request)
    await service.logout(body.refresh_token)
    return MessageResponse(message="已成功登出")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> UserResponse:
    """获取当前登录用户信息。"""
    return _user_response(current_user)
