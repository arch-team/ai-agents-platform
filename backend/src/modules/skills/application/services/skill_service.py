"""Skill 应用服务。"""

from src.modules.skills.application.dto.skill_dto import (
    CreateSkillDTO,
    SkillDTO,
    UpdateSkillDTO,
)
from src.modules.skills.application.interfaces.skill_file_manager import ISkillFileManager
from src.modules.skills.domain.entities.skill import Skill
from src.modules.skills.domain.exceptions import SkillNotFoundError
from src.modules.skills.domain.repositories.skill_repository import ISkillRepository
from src.modules.skills.domain.value_objects.skill_category import SkillCategory
from src.modules.skills.domain.value_objects.skill_status import SkillStatus
from src.shared.application.dtos import PagedResult
from src.shared.application.ownership import check_ownership, get_or_raise
from src.shared.domain.event_bus import event_bus  # noqa: F401
from src.shared.domain.exceptions import InvalidStateTransitionError


class SkillService:
    """Skill 业务服务，编排 CRUD + 文件系统联动 + 发布流程。"""

    def __init__(self, repository: ISkillRepository, file_manager: ISkillFileManager) -> None:
        self._repository = repository
        self._file_manager = file_manager

    async def create_skill(self, dto: CreateSkillDTO, creator_id: int) -> SkillDTO:
        """创建 Skill (DRAFT)。如果提供 skill_md，同时保存 SKILL.md 草稿。"""
        file_path = ""
        if dto.skill_md:
            file_path = await self._file_manager.save_draft(
                dto.name,
                dto.skill_md,
                references=dto.references,
            )

        skill = Skill(
            name=dto.name,
            description=dto.description,
            category=SkillCategory(dto.category),
            trigger_description=dto.trigger_description,
            creator_id=creator_id,
            file_path=file_path,
        )
        created = await self._repository.create(skill)
        return self._to_dto(created)

    async def get_skill(self, skill_id: int) -> SkillDTO:
        """获取 Skill 详情。

        Raises:
            SkillNotFoundError: Skill 不存在
        """
        skill = await self._get_skill_or_raise(skill_id)
        return self._to_dto(skill)

    async def get_skill_with_content(self, skill_id: int) -> tuple[SkillDTO, str]:
        """获取 Skill 详情 + SKILL.md 内容。"""
        skill = await self._get_skill_or_raise(skill_id)
        content = ""
        if skill.file_path:
            content = await self._file_manager.read_skill_md(skill.file_path)
        return self._to_dto(skill), content

    async def update_skill(self, skill_id: int, dto: UpdateSkillDTO, operator_id: int) -> SkillDTO:
        """更新 Skill。仅 DRAFT 可编辑。

        Raises:
            SkillNotFoundError, ForbiddenError, InvalidStateTransitionError
        """
        skill = await self._get_owned_skill(skill_id, operator_id)

        if skill.status != SkillStatus.DRAFT:
            raise InvalidStateTransitionError(
                entity_type="Skill",
                current_state=skill.status.value,
                target_state="updated",
            )

        # 更新元信息字段
        if dto.name is not None:
            skill.name = dto.name
        if dto.description is not None:
            skill.description = dto.description
        if dto.category is not None:
            skill.category = SkillCategory(dto.category)
        if dto.trigger_description is not None:
            skill.trigger_description = dto.trigger_description

        # 更新文件内容
        if dto.skill_md is not None and skill.file_path:
            await self._file_manager.update_draft(skill.file_path, dto.skill_md, references=dto.references)

        skill.touch()
        updated = await self._repository.update(skill)
        return self._to_dto(updated)

    async def delete_skill(self, skill_id: int, operator_id: int) -> None:
        """删除 Skill。仅 DRAFT 可删除，同时清理文件。

        Raises:
            SkillNotFoundError, ForbiddenError, InvalidStateTransitionError
        """
        skill = await self._get_owned_skill(skill_id, operator_id)

        if skill.status != SkillStatus.DRAFT:
            raise InvalidStateTransitionError(
                entity_type="Skill",
                current_state=skill.status.value,
                target_state="deleted",
            )

        if skill.file_path:
            await self._file_manager.delete_draft(skill.file_path)
        await self._repository.delete(skill_id)

    async def publish_skill(self, skill_id: int, operator_id: int) -> SkillDTO:
        """发布 Skill: 文件系统版本化复制 + 实体状态转换 + 持久化。

        Raises:
            SkillNotFoundError, ForbiddenError, InvalidStateTransitionError, ValidationError
        """
        skill = await self._get_owned_skill(skill_id, operator_id)
        published_path = await self._file_manager.publish(skill.file_path, skill.name, version=skill.version)
        skill.update_file_path(published_path)
        skill.publish()
        updated = await self._repository.update(skill)
        return self._to_dto(updated)

    async def archive_skill(self, skill_id: int, operator_id: int) -> SkillDTO:
        """归档 Skill。

        Raises:
            SkillNotFoundError, ForbiddenError, InvalidStateTransitionError
        """
        skill = await self._get_owned_skill(skill_id, operator_id)
        skill.archive()
        updated = await self._repository.update(skill)
        return self._to_dto(updated)

    async def list_published_skills(
        self,
        *,
        category: SkillCategory | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[SkillDTO]:
        """获取已发布的 Skill 列表。"""
        offset = (page - 1) * page_size

        if keyword:
            skills = await self._repository.search(keyword, category=category, offset=offset, limit=page_size)
        elif category:
            skills = await self._repository.list_by_category(category, offset=offset, limit=page_size)
        else:
            skills = await self._repository.list_published(offset=offset, limit=page_size)

        total = await self._repository.count()
        return PagedResult(items=[self._to_dto(s) for s in skills], total=total, page=page, page_size=page_size)

    async def list_my_skills(self, creator_id: int, *, page: int = 1, page_size: int = 20) -> PagedResult[SkillDTO]:
        """获取创建者自己的 Skill 列表。"""
        offset = (page - 1) * page_size
        skills = await self._repository.list_by_creator(creator_id, offset=offset, limit=page_size)
        total = await self._repository.count_by_creator(creator_id)
        return PagedResult(items=[self._to_dto(s) for s in skills], total=total, page=page, page_size=page_size)

    # ── 内部辅助 ──

    async def _get_skill_or_raise(self, skill_id: int) -> Skill:
        return await get_or_raise(self._repository, skill_id, SkillNotFoundError, skill_id)

    async def _get_owned_skill(self, skill_id: int, operator_id: int) -> Skill:
        skill = await self._get_skill_or_raise(skill_id)
        check_ownership(skill, operator_id, owner_field="creator_id", error_code="FORBIDDEN_SKILL")
        return skill

    @staticmethod
    def _to_dto(skill: Skill) -> SkillDTO:
        id_, created_at, updated_at = skill.require_persisted()
        return SkillDTO(
            id=id_,
            name=skill.name,
            description=skill.description,
            category=skill.category.value,
            trigger_description=skill.trigger_description,
            status=skill.status.value,
            creator_id=skill.creator_id,
            version=skill.version,
            usage_count=skill.usage_count,
            file_path=skill.file_path,
            created_at=created_at,
            updated_at=updated_at,
        )
