"""ISkillCreator 的具体实现，用于 builder 模块的跨模块 Skill 创建。"""

from src.modules.skills.application.dto.skill_dto import CreateSkillDTO
from src.modules.skills.application.services.skill_service import SkillService
from src.shared.domain.interfaces.skill_creator import (
    CreatedSkillInfo,
    CreateSkillRequest,
    ISkillCreator,
)


class SkillCreatorImpl(ISkillCreator):
    """通过 SkillService 实现 ISkillCreator 接口。"""

    def __init__(self, skill_service: SkillService) -> None:
        self._skill_service = skill_service

    async def create_skill(self, request: CreateSkillRequest, creator_id: int) -> CreatedSkillInfo:
        """创建 Skill (DRAFT): 文件 + DB 记录。"""
        dto = CreateSkillDTO(
            name=request.name,
            description=request.description,
            category=request.category,
            trigger_description=request.trigger_description,
            skill_md=request.skill_md,
        )
        skill_dto = await self._skill_service.create_skill(dto, creator_id)
        return CreatedSkillInfo(
            id=skill_dto.id,
            name=skill_dto.name,
            file_path=skill_dto.file_path,
            version=skill_dto.version,
        )

    async def publish_skill(self, skill_id: int, operator_id: int) -> CreatedSkillInfo:
        """发布 Skill: DRAFT → PUBLISHED。"""
        skill_dto = await self._skill_service.publish_skill(skill_id, operator_id)
        return CreatedSkillInfo(
            id=skill_dto.id,
            name=skill_dto.name,
            file_path=skill_dto.file_path,
            version=skill_dto.version,
        )
