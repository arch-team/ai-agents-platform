"""ISkillQuerier 实现。"""

from src.modules.skills.domain.repositories.skill_repository import ISkillRepository
from src.modules.skills.domain.value_objects.skill_category import SkillCategory
from src.modules.skills.domain.value_objects.skill_status import SkillStatus
from src.shared.domain.interfaces.skill_querier import ISkillQuerier, SkillInfo, SkillSummary


class SkillQuerierImpl(ISkillQuerier):
    """基于 ISkillRepository 的跨模块查询实现。"""

    def __init__(self, skill_repository: ISkillRepository) -> None:
        self._repository = skill_repository

    async def get_published_skills(self, skill_ids: list[int]) -> list[SkillInfo]:
        result: list[SkillInfo] = []
        for skill_id in skill_ids:
            skill = await self._repository.get_by_id(skill_id)
            if skill and skill.status == SkillStatus.PUBLISHED:
                result.append(
                    SkillInfo(
                        id=skill.id or 0,
                        name=skill.name,
                        description=skill.description,
                        category=skill.category.value,
                        trigger_description=skill.trigger_description,
                        version=skill.version,
                        file_path=skill.file_path,
                    ),
                )
        return result

    async def list_published_skills(self, *, category: str | None = None, limit: int = 20) -> list[SkillSummary]:
        if category:
            skills = await self._repository.list_by_category(SkillCategory(category), limit=limit)
        else:
            skills = await self._repository.list_published(limit=limit)
        return [
            SkillSummary(
                id=s.id or 0,
                name=s.name,
                description=s.description,
                category=s.category.value,
            )
            for s in skills
        ]
