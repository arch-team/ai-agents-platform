"""Skills API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.skills.api.dependencies import get_skill_service
from src.modules.skills.api.schemas.requests import CreateSkillRequest, UpdateSkillRequest
from src.modules.skills.api.schemas.responses import SkillDetailResponse, SkillListResponse, SkillResponse
from src.modules.skills.application.dto.skill_dto import CreateSkillDTO, SkillDTO, UpdateSkillDTO
from src.modules.skills.application.services.skill_service import SkillService
from src.modules.skills.domain.value_objects.skill_category import SkillCategory
from src.shared.api.schemas import calc_total_pages


router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

ServiceDep = Annotated[SkillService, Depends(get_skill_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


def _to_response(dto: SkillDTO) -> SkillResponse:
    return SkillResponse(
        id=dto.id,
        name=dto.name,
        description=dto.description,
        category=dto.category,
        trigger_description=dto.trigger_description,
        status=dto.status,
        creator_id=dto.creator_id,
        version=dto.version,
        usage_count=dto.usage_count,
        file_path=dto.file_path,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_skill(request: CreateSkillRequest, service: ServiceDep, current_user: CurrentUserDep) -> SkillResponse:
    """创建 Skill (DRAFT)。"""
    dto = CreateSkillDTO(**request.model_dump())
    skill = await service.create_skill(dto, current_user.id)
    return _to_response(skill)


@router.get("")
async def list_skills(
    service: ServiceDep,
    current_user: CurrentUserDep,
    category: Annotated[str | None, Query()] = None,
    keyword: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SkillListResponse:
    """获取已发布的 Skill 列表 (支持分类/关键词搜索)。"""
    cat = SkillCategory(category) if category else None
    paged = await service.list_published_skills(category=cat, keyword=keyword, page=page, page_size=page_size)
    return SkillListResponse(
        items=[_to_response(s) for s in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/mine")
async def list_my_skills(
    service: ServiceDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SkillListResponse:
    """获取当前用户创建的 Skill 列表。"""
    paged = await service.list_my_skills(creator_id=current_user.id, page=page, page_size=page_size)
    return SkillListResponse(
        items=[_to_response(s) for s in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/{skill_id}")
async def get_skill(skill_id: int, service: ServiceDep, current_user: CurrentUserDep) -> SkillDetailResponse:
    """获取 Skill 详情 (含 SKILL.md 内容)。"""
    dto, content = await service.get_skill_with_content(skill_id)
    return SkillDetailResponse(
        **_to_response(dto).model_dump(),
        skill_md_content=content,
    )


@router.put("/{skill_id}")
async def update_skill(
    skill_id: int,
    request: UpdateSkillRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> SkillResponse:
    """更新 Skill (仅 DRAFT)。"""
    dto = UpdateSkillDTO(**request.model_dump())
    skill = await service.update_skill(skill_id, dto, current_user.id)
    return _to_response(skill)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(skill_id: int, service: ServiceDep, current_user: CurrentUserDep) -> None:
    """删除 Skill (仅 DRAFT，同时清理文件)。"""
    await service.delete_skill(skill_id, current_user.id)


@router.post("/{skill_id}/publish")
async def publish_skill(skill_id: int, service: ServiceDep, current_user: CurrentUserDep) -> SkillResponse:
    """发布 Skill 到 Skill 库。"""
    skill = await service.publish_skill(skill_id, current_user.id)
    return _to_response(skill)


@router.post("/{skill_id}/archive")
async def archive_skill(skill_id: int, service: ServiceDep, current_user: CurrentUserDep) -> SkillResponse:
    """归档 Skill。"""
    skill = await service.archive_skill(skill_id, current_user.id)
    return _to_response(skill)
