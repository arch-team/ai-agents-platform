"""Skill 仓库实现。"""

from sqlalchemy import ColumnElement, or_, select

from src.modules.skills.domain.entities.skill import Skill
from src.modules.skills.domain.repositories.skill_repository import ISkillRepository
from src.modules.skills.domain.value_objects.skill_category import SkillCategory
from src.modules.skills.domain.value_objects.skill_status import SkillStatus
from src.modules.skills.infrastructure.persistence.models.skill_model import SkillModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class SkillRepositoryImpl(PydanticRepository[Skill, SkillModel, int], ISkillRepository):
    """Skill 仓库的 SQLAlchemy 实现。"""

    entity_class = Skill
    model_class = SkillModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "name",
            "description",
            "category",
            "trigger_description",
            "status",
            "version",
            "usage_count",
            "file_path",
        },
    )

    def _to_entity(self, model: SkillModel) -> Skill:
        return Skill(
            id=model.id,
            name=model.name,
            description=model.description,
            category=SkillCategory(model.category),
            trigger_description=model.trigger_description,
            status=SkillStatus(model.status),
            creator_id=model.creator_id,
            version=model.version,
            usage_count=model.usage_count,
            file_path=model.file_path,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Skill) -> SkillModel:
        return SkillModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            category=entity.category.value,
            trigger_description=entity.trigger_description,
            status=entity.status.value,
            creator_id=entity.creator_id,
            version=entity.version,
            usage_count=entity.usage_count,
            file_path=entity.file_path,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _get_update_data(self, entity: Skill) -> dict[str, object]:
        return {
            "name": entity.name,
            "description": entity.description,
            "category": entity.category.value,
            "trigger_description": entity.trigger_description,
            "status": entity.status.value,
            "version": entity.version,
            "usage_count": entity.usage_count,
            "file_path": entity.file_path,
        }

    # ── 查询辅助 ──

    @staticmethod
    def _published_filter() -> ColumnElement[bool]:
        return SkillModel.status == SkillStatus.PUBLISHED.value

    # ── 接口实现 ──

    async def get_by_name(self, name: str) -> Skill | None:
        stmt = select(SkillModel).where(SkillModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_published(self, *, offset: int = 0, limit: int = 20) -> list[Skill]:
        return await self._list_where(self._published_filter(), offset=offset, limit=limit)

    async def list_by_creator(self, creator_id: int, *, offset: int = 0, limit: int = 20) -> list[Skill]:
        return await self._list_where(SkillModel.creator_id == creator_id, offset=offset, limit=limit)

    async def list_by_category(self, category: SkillCategory, *, offset: int = 0, limit: int = 20) -> list[Skill]:
        return await self._list_where(
            self._published_filter(),
            SkillModel.category == category.value,
            offset=offset,
            limit=limit,
        )

    async def search(
        self,
        keyword: str,
        *,
        category: SkillCategory | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Skill]:
        filters: list[ColumnElement[bool]] = [
            self._published_filter(),
            or_(
                SkillModel.name.contains(keyword),
                SkillModel.description.contains(keyword),
                SkillModel.trigger_description.contains(keyword),
            ),
        ]
        if category is not None:
            filters.append(SkillModel.category == category.value)
        return await self._list_where(*filters, offset=offset, limit=limit)

    async def count_by_creator(self, creator_id: int) -> int:
        return await self._count_where(SkillModel.creator_id == creator_id)

    async def get_by_ids(self, ids: list[int]) -> list[Skill]:
        if not ids:
            return []
        stmt = select(SkillModel).where(SkillModel.id.in_(ids))
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def increment_usage_count(self, skill_id: int) -> None:
        model = await self._get_model_or_raise(skill_id)
        model.usage_count += 1
        await self._session.flush()
