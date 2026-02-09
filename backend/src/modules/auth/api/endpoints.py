"""Auth API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.modules.auth.api.dependencies import get_current_user, get_user_service
from src.modules.auth.api.schemas.requests import LoginRequest, RegisterRequest
from src.modules.auth.api.schemas.responses import TokenResponse, UserResponse
from src.modules.auth.application.dto.user_dto import CreateUserDTO, LoginDTO, UserDTO
from src.modules.auth.application.services.user_service import UserService


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


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
async def register(
    request: RegisterRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """注册新用户。"""
    dto = CreateUserDTO(email=request.email, password=request.password, name=request.name)
    user = await service.register(dto)
    return _user_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    """用户登录，返回 JWT token。"""
    dto = LoginDTO(email=request.email, password=request.password)
    token = await service.login(dto)
    return TokenResponse(access_token=token.access_token, token_type=token.token_type)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> UserResponse:
    """获取当前登录用户信息。"""
    return _user_response(current_user)
