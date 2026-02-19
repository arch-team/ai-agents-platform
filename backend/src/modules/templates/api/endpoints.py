"""Template API 端点。"""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.templates.api.dependencies import get_template_service
from src.modules.templates.api.schemas.requests import CreateTemplateRequest, UpdateTemplateRequest
from src.modules.templates.api.schemas.responses import TemplateListResponse, TemplateResponse
from src.modules.templates.application.dto.template_dto import CreateTemplateDTO, TemplateDTO, UpdateTemplateDTO
from src.modules.templates.application.services.template_service import TemplateService
from src.shared.api.schemas import calc_total_pages


router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

ServiceDep = Annotated[TemplateService, Depends(get_template_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


def _to_response(dto: TemplateDTO) -> TemplateResponse:
    return TemplateResponse(**asdict(dto))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_template(
    request: CreateTemplateRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> TemplateResponse:
    """创建模板。"""
    dto = CreateTemplateDTO(**request.model_dump())
    result = await service.create_template(dto, current_user.id)
    return _to_response(result)


@router.get("")
async def list_templates(
    service: ServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
) -> TemplateListResponse:
    """获取模板列表 (公开已发布 + 搜索/分类筛选)。"""
    paged = await service.list_templates(page=page, page_size=page_size, category=category, keyword=keyword)
    return TemplateListResponse(
        items=[_to_response(t) for t in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/mine")
async def list_my_templates(
    service: ServiceDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TemplateListResponse:
    """获取我的模板列表 (含所有状态)。"""
    paged = await service.list_my_templates(current_user.id, page=page, page_size=page_size)
    return TemplateListResponse(
        items=[_to_response(t) for t in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/{template_id}")
async def get_template(template_id: int, service: ServiceDep) -> TemplateResponse:
    """获取模板详情。"""
    result = await service.get_template(template_id)
    return _to_response(result)


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    request: UpdateTemplateRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> TemplateResponse:
    """更新模板 (仅 DRAFT 状态)。"""
    dto = UpdateTemplateDTO(**request.model_dump())
    result = await service.update_template(template_id, dto, current_user.id)
    return _to_response(result)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: int, service: ServiceDep, current_user: CurrentUserDep) -> None:
    """删除模板 (仅 DRAFT 状态)。"""
    await service.delete_template(template_id, current_user.id)


@router.post("/{template_id}/publish")
async def publish_template(template_id: int, service: ServiceDep, current_user: CurrentUserDep) -> TemplateResponse:
    """发布模板 (DRAFT -> PUBLISHED)。"""
    result = await service.publish_template(template_id, current_user.id)
    return _to_response(result)


@router.post("/{template_id}/archive")
async def archive_template(template_id: int, service: ServiceDep, current_user: CurrentUserDep) -> TemplateResponse:
    """归档模板 (PUBLISHED -> ARCHIVED)。"""
    result = await service.archive_template(template_id, current_user.id)
    return _to_response(result)
