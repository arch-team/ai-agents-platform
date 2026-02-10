"""Tool Catalog API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.dependencies import get_current_user, require_role
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.auth.domain.value_objects.role import Role
from src.modules.tool_catalog.api.dependencies import get_tool_service
from src.modules.tool_catalog.api.schemas.requests import (
    CreateToolRequest,
    RejectToolRequest,
    UpdateToolRequest,
)
from src.modules.tool_catalog.api.schemas.responses import (
    ToolConfigResponse,
    ToolListResponse,
    ToolResponse,
)
from src.modules.tool_catalog.application.dto.tool_dto import (
    CreateToolDTO,
    PagedToolDTO,
    ToolDTO,
    UpdateToolDTO,
)
from src.modules.tool_catalog.application.services.tool_service import ToolCatalogService
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.shared.api.schemas import calc_total_pages


router = APIRouter(prefix="/api/v1/tools", tags=["tools"])

# 类型别名简化重复的依赖注入声明
ServiceDep = Annotated[ToolCatalogService, Depends(get_tool_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]
AdminUserDep = Annotated[UserDTO, Depends(require_role(Role.ADMIN))]


def _to_response(dto: ToolDTO) -> ToolResponse:
    return ToolResponse(
        id=dto.id,
        name=dto.name,
        description=dto.description,
        tool_type=dto.tool_type,
        version=dto.version,
        status=dto.status,
        creator_id=dto.creator_id,
        config=ToolConfigResponse(
            server_url=dto.server_url,
            transport=dto.transport,
            endpoint_url=dto.endpoint_url,
            method=dto.method,
            runtime=dto.runtime,
            handler=dto.handler,
            code_uri=dto.code_uri,
            auth_type=dto.auth_type,
        ),
        allowed_roles=dto.allowed_roles,
        reviewer_id=dto.reviewer_id,
        review_comment=dto.review_comment,
        reviewed_at=dto.reviewed_at,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


def _to_list_response(paged: PagedToolDTO, page_size: int) -> ToolListResponse:
    return ToolListResponse(
        items=[_to_response(t) for t in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    request: CreateToolRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ToolResponse:
    """创建 Tool。ADMIN 或 DEVELOPER 角色可操作。"""
    dto = CreateToolDTO(**request.model_dump())
    tool = await service.create_tool(dto, current_user.id)
    return _to_response(tool)


@router.get("", response_model=ToolListResponse)
async def list_tools(
    service: ServiceDep,
    current_user: CurrentUserDep,  # noqa: ARG001
    status_filter: Annotated[ToolStatus | None, Query(alias="status")] = None,
    type_filter: Annotated[ToolType | None, Query(alias="type")] = None,
    keyword: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ToolListResponse:
    """获取 Tool 列表，支持多维筛选。"""
    paged = await service.list_tools(
        status=status_filter,
        tool_type=type_filter,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return _to_list_response(paged, page_size)


# NOTE: /approved must be registered before /{tool_id}
@router.get("/approved", response_model=ToolListResponse)
async def list_approved_tools(
    service: ServiceDep,
    current_user: CurrentUserDep,  # noqa: ARG001
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ToolListResponse:
    """获取已批准的 Tool 列表。任意认证用户可访问。"""
    paged = await service.list_approved_tools(page=page, page_size=page_size)
    return _to_list_response(paged, page_size)


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,  # noqa: ARG001
) -> ToolResponse:
    """获取 Tool 详情。"""
    tool = await service.get_tool(tool_id)
    return _to_response(tool)


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    request: UpdateToolRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ToolResponse:
    """更新 Tool。仅 creator 可操作，仅 DRAFT/REJECTED 可编辑。"""
    dto = UpdateToolDTO(**request.model_dump())
    tool = await service.update_tool(tool_id, dto, current_user.id)
    return _to_response(tool)


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """删除 Tool。仅 creator 可操作，仅 DRAFT 状态可删除。"""
    await service.delete_tool(tool_id, current_user.id)


@router.post("/{tool_id}/submit", response_model=ToolResponse)
async def submit_for_review(
    tool_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ToolResponse:
    """提交 Tool 审批。仅 creator 可操作。"""
    tool = await service.submit_for_review(tool_id, current_user.id)
    return _to_response(tool)


@router.post("/{tool_id}/approve", response_model=ToolResponse)
async def approve_tool(
    tool_id: int,
    service: ServiceDep,
    current_user: AdminUserDep,
) -> ToolResponse:
    """审批通过 Tool。仅 ADMIN 可操作。"""
    tool = await service.approve_tool(tool_id, current_user.id)
    return _to_response(tool)


@router.post("/{tool_id}/reject", response_model=ToolResponse)
async def reject_tool(
    tool_id: int,
    request: RejectToolRequest,
    service: ServiceDep,
    current_user: AdminUserDep,
) -> ToolResponse:
    """审批拒绝 Tool。仅 ADMIN 可操作。"""
    tool = await service.reject_tool(tool_id, current_user.id, request.comment)
    return _to_response(tool)


@router.post("/{tool_id}/deprecate", response_model=ToolResponse)
async def deprecate_tool(
    tool_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ToolResponse:
    """废弃 Tool。creator 或 ADMIN 可操作。"""
    tool = await service.deprecate_tool(tool_id, current_user.id)
    return _to_response(tool)
