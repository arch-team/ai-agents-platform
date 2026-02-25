"""Template 仓库实现。"""

from sqlalchemy import ColumnElement, or_, select, update

from src.modules.templates.domain.entities.template import Template
from src.modules.templates.domain.repositories.template_repository import ITemplateRepository
from src.modules.templates.domain.value_objects.template_category import TemplateCategory
from src.modules.templates.domain.value_objects.template_config import TemplateConfig
from src.modules.templates.domain.value_objects.template_status import TemplateStatus
from src.modules.templates.infrastructure.persistence.models.template_model import TemplateModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class TemplateRepositoryImpl(PydanticRepository[Template, TemplateModel, int], ITemplateRepository):
    """Template 仓库的 SQLAlchemy 实现。"""

    entity_class = Template
    model_class = TemplateModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "name",
            "description",
            "category",
            "status",
            "system_prompt",
            "model_id",
            "temperature",
            "max_tokens",
            "tool_ids",
            "knowledge_base_ids",
            "tags",
            "usage_count",
            "is_featured",
            "updated_at",
        },
    )

    def _flatten_config(self, entity: Template) -> dict[str, object]:
        """将 Entity 的 config 和扁平字段展开为 Model 列数据。"""
        return {
            "name": entity.name,
            "description": entity.description,
            "category": entity.category.value,
            "status": entity.status.value,
            "system_prompt": entity.config.system_prompt,
            "model_id": entity.config.model_id,
            "temperature": entity.config.temperature,
            "max_tokens": entity.config.max_tokens,
            "tool_ids": list(entity.config.tool_ids),
            "knowledge_base_ids": list(entity.config.knowledge_base_ids),
            "tags": list(entity.tags),
            "usage_count": entity.usage_count,
            "is_featured": entity.is_featured,
            "updated_at": entity.updated_at,
        }

    def _to_model(self, entity: Template) -> TemplateModel:
        return TemplateModel(
            id=entity.id,
            creator_id=entity.creator_id,
            created_at=entity.created_at,
            **self._flatten_config(entity),
        )

    def _to_entity(self, model: TemplateModel) -> Template:
        return Template(
            id=model.id,
            name=model.name,
            description=model.description,
            category=TemplateCategory(model.category),
            status=TemplateStatus(model.status),
            creator_id=model.creator_id,
            config=TemplateConfig(
                system_prompt=model.system_prompt,
                model_id=model.model_id,
                temperature=model.temperature,
                max_tokens=model.max_tokens,
                tool_ids=list(model.tool_ids) if model.tool_ids else [],
                knowledge_base_ids=list(model.knowledge_base_ids) if model.knowledge_base_ids else [],
            ),
            tags=list(model.tags) if model.tags else [],
            usage_count=model.usage_count,
            is_featured=model.is_featured,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _get_update_data(self, entity: Template) -> dict[str, object]:
        return self._flatten_config(entity)

    # ── 查询辅助方法 ──

    @staticmethod
    def _build_search_conditions(
        keyword: str,
        category: TemplateCategory | None,
        *,
        published_only: bool = True,
    ) -> list[ColumnElement[bool]]:
        """构建搜索查询条件。"""
        conditions: list[ColumnElement[bool]] = []
        if published_only:
            conditions.append(TemplateModel.status == TemplateStatus.PUBLISHED.value)
        if keyword:
            like_pattern = f"%{keyword}%"
            conditions.append(or_(TemplateModel.name.like(like_pattern), TemplateModel.description.like(like_pattern)))
        if category:
            conditions.append(TemplateModel.category == category.value)
        return conditions

    # ── 接口实现 ──

    async def get_by_name(self, name: str) -> Template | None:  # noqa: D102
        stmt = select(TemplateModel).where(TemplateModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_published(self, *, offset: int = 0, limit: int = 20) -> list[Template]:  # noqa: D102
        stmt = (
            select(TemplateModel)
            .where(TemplateModel.status == TemplateStatus.PUBLISHED.value)
            .offset(offset)
            .limit(limit)
            .order_by(TemplateModel.usage_count.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_creator(self, creator_id: int, *, offset: int = 0, limit: int = 20) -> list[Template]:  # noqa: D102
        stmt = (
            select(TemplateModel)
            .where(TemplateModel.creator_id == creator_id)
            .offset(offset)
            .limit(limit)
            .order_by(TemplateModel.id.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_category(self, category: TemplateCategory, *, offset: int = 0, limit: int = 20) -> list[Template]:  # noqa: D102
        stmt = (
            select(TemplateModel)
            .where(TemplateModel.category == category.value, TemplateModel.status == TemplateStatus.PUBLISHED.value)
            .offset(offset)
            .limit(limit)
            .order_by(TemplateModel.usage_count.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def search(  # noqa: D102
        self,
        keyword: str,
        *,
        category: TemplateCategory | None = None,
        tags: list[str] | None = None,  # noqa: ARG002
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        conditions = self._build_search_conditions(keyword, category)
        stmt = select(TemplateModel)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.offset(offset).limit(limit).order_by(TemplateModel.id.desc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_search(  # noqa: D102
        self,
        keyword: str,
        *,
        category: TemplateCategory | None = None,
        tags: list[str] | None = None,  # noqa: ARG002
    ) -> int:
        conditions = self._build_search_conditions(keyword, category)
        return await self._count_where(*conditions) if conditions else await self.count()

    async def search_with_total(
        self,
        keyword: str,
        *,
        category: TemplateCategory | None = None,
        tags: list[str] | None = None,  # noqa: ARG002
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Template], int]:
        """单次查询同时返回数据和总数 (COUNT OVER 窗口函数, 单次 DB 往返)。"""
        from sqlalchemy import func as sa_func

        conditions = self._build_search_conditions(keyword, category)
        # COUNT(*) OVER() 在 LIMIT 之前计算总数, 一次查询同时得到数据和总数
        total_col = sa_func.count(TemplateModel.id).over().label("_total")
        stmt = select(TemplateModel, total_col)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.offset(offset).limit(limit).order_by(TemplateModel.id.desc())
        result = await self._session.execute(stmt)
        rows = result.all()
        if not rows:
            return [], 0
        total: int = rows[0]._total
        items = [self._to_entity(row[0]) for row in rows]
        return items, total

    async def count_by_creator(self, creator_id: int) -> int:  # noqa: D102
        return await self._count_where(TemplateModel.creator_id == creator_id)

    async def increment_usage_count(self, template_id: int) -> None:  # noqa: D102
        stmt = (
            update(TemplateModel)
            .where(TemplateModel.id == template_id)
            .values(usage_count=TemplateModel.usage_count + 1)
        )
        await self._session.execute(stmt)
        await self._session.flush()
