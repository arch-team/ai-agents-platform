"""Admin 用户管理 API 端点。"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.dependencies import get_user_service, require_role
from src.modules.auth.api.schemas.admin_requests import AdminCreateUserRequest, ChangeRoleRequest
from src.modules.auth.api.schemas.admin_responses import UserListResponse
from src.modules.auth.api.schemas.responses import UserResponse
from src.modules.auth.application.dto.user_dto import AdminCreateUserDTO, ChangeRoleDTO, UserDTO
from src.modules.auth.application.services.user_service import UserService
from src.modules.auth.domain.value_objects.role import Role


logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

AdminUserDep = Annotated[UserDTO, Depends(require_role(Role.ADMIN))]


def _user_response(user: UserDTO) -> UserResponse:
    """将 UserDTO 转换为 API 响应模型。"""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
    )


@router.get("/users", response_model=UserListResponse)
async def list_users(
    _current_user: AdminUserDep,
    service: Annotated[UserService, Depends(get_user_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UserListResponse:
    """列出所有用户（分页，仅管理员）。"""
    result = await service.list_all_users(page=page, page_size=page_size)
    return UserListResponse(
        items=[_user_response(u) for u in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    _current_user: AdminUserDep,
    body: AdminCreateUserRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """管理员创建用户（可指定角色，仅管理员）。"""
    dto = AdminCreateUserDTO(
        email=body.email,
        password=body.password,
        name=body.name,
        role=body.role,
    )
    user = await service.create_user_with_role(dto)
    return _user_response(user)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    current_user: AdminUserDep,
    body: ChangeRoleRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """变更用户角色（仅管理员）。"""
    dto = ChangeRoleDTO(user_id=user_id, new_role=body.role)
    user = await service.change_user_role(dto, operator_id=current_user.id)
    return _user_response(user)
