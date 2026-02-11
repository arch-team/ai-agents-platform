"""Template 仓库实现。"""

from sqlalchemy import ColumnElement, or_, select, update

from src.modules.templates.domain.entities.template import Template
from src.modules.templates.domain.repositories.template_repository import (
    ITemplateRepository,
)
from src.modules.templates.domain.value_objects.template_category import (
    TemplateCategory,
)
from src.modules.templates.domain.value_objects.template_config import TemplateConfig
from src.modules.templates.domain.value_objects.template_status import TemplateStatus
from src.modules.templates.infrastructure.persistence.models.template_model import (
    TemplateModel,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class TemplateRepositoryImpl(
    PydanticRepository[Template, TemplateModel, int],
    ITemplateRepository,
):
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

    def _to_model(self, entity: Template) -> TemplateModel:
        """Entity -> ORM Model 转换 (扁平化 TemplateConfig)。"""
        return TemplateModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            category=entity.category.value,
            status=entity.status.value,
            creator_id=entity.creator_id,
            system_prompt=entity.config.system_prompt,
            model_id=entity.config.model_id,
            temperature=entity.config.temperature,
            max_tokens=entity.config.max_tokens,
            tool_ids=list(entity.config.tool_ids),
            knowledge_base_ids=list(entity.config.knowledge_base_ids),
            tags=list(entity.tags),
            usage_count=entity.usage_count,
            is_featured=entity.is_featured,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, model: TemplateModel) -> Template:
        """ORM Model -> Entity 转换 (组装 TemplateConfig)。"""
        config = TemplateConfig(
            system_prompt=model.system_prompt,
            model_id=model.model_id,
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            tool_ids=list(model.tool_ids) if model.tool_ids else [],
            knowledge_base_ids=list(model.knowledge_base_ids) if model.knowledge_base_ids else [],
        )
        return Template(
            id=model.id,
            name=model.name,
            description=model.description,
            category=TemplateCategory(model.category),
            status=TemplateStatus(model.status),
            creator_id=model.creator_id,
            config=config,
            tags=list(model.tags) if model.tags else [],
            usage_count=model.usage_count,
            is_featured=model.is_featured,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _get_update_data(self, entity: Template) -> dict[str, object]:
        """提取可更新字段数据 (扁平化 TemplateConfig)。"""
        data: dict[str, object] = {
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
        return {k: v for k, v in data.items() if k in self._updatable_fields}

    async def get_by_name(self, name: str) -> Template | None:
        """按名称查询模板。"""
        stmt = select(TemplateModel).where(TemplateModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_published(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        """获取已发布模板列表，按使用次数降序。"""
        stmt = (
            select(TemplateModel)
            .where(TemplateModel.status == "published")
            .offset(offset)
            .limit(limit)
            .order_by(TemplateModel.usage_count.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_creator(
        self,
        creator_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        """按创建者查询模板列表。"""
        stmt = (
            select(TemplateModel)
            .where(TemplateModel.creator_id == creator_id)
            .offset(offset)
            .limit(limit)
            .order_by(TemplateModel.id.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_category(
        self,
        category: TemplateCategory,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        """按分类查询已发布模板列表。"""
        stmt = (
            select(TemplateModel)
            .where(
                TemplateModel.category == category.value,
                TemplateModel.status == "published",
            )
            .offset(offset)
            .limit(limit)
            .order_by(TemplateModel.usage_count.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def search(
        self,
        keyword: str,
        *,
        category: TemplateCategory | None = None,
        tags: list[str] | None = None,  # noqa: ARG002
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        """搜索模板。"""
        stmt = select(TemplateModel)

        conditions = []
        if keyword:
            like_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    TemplateModel.name.like(like_pattern),
                    TemplateModel.description.like(like_pattern),
                ),
            )
        if category:
            conditions.append(TemplateModel.category == category.value)

        if conditions:
            stmt = stmt.where(*conditions)

        stmt = stmt.offset(offset).limit(limit).order_by(TemplateModel.id.desc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_search(
        self,
        keyword: str,
        *,
        category: TemplateCategory | None = None,
        tags: list[str] | None = None,  # noqa: ARG002
    ) -> int:
        """按搜索条件统计模板数量。"""
        conditions: list[ColumnElement[bool]] = []
        if keyword:
            like_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    TemplateModel.name.like(like_pattern),
                    TemplateModel.description.like(like_pattern),
                ),
            )
        if category:
            conditions.append(TemplateModel.category == category.value)

        return await self._count_where(*conditions) if conditions else await self.count()

    async def count_by_creator(self, creator_id: int) -> int:
        """按创建者统计模板数量。"""
        return await self._count_where(TemplateModel.creator_id == creator_id)

    async def increment_usage_count(self, template_id: int) -> None:
        """增加模板使用次数。"""
        stmt = (
            update(TemplateModel)
            .where(TemplateModel.id == template_id)
            .values(usage_count=TemplateModel.usage_count + 1)
        )
        await self._session.execute(stmt)
        await self._session.flush()
