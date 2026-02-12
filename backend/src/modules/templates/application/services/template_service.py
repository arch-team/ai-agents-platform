"""Template 应用服务。"""

import asyncio
from dataclasses import replace

from src.modules.templates.application.dto.template_dto import (
    CreateTemplateDTO,
    TemplateDTO,
    UpdateTemplateDTO,
)
from src.modules.templates.domain.entities.template import Template
from src.modules.templates.domain.events import (
    TemplateArchivedEvent,
    TemplateCreatedEvent,
    TemplatePublishedEvent,
)
from src.modules.templates.domain.exceptions import (
    DuplicateTemplateNameError,
    TemplateNotFoundError,
)
from src.modules.templates.domain.repositories.template_repository import (
    ITemplateRepository,
)
from src.modules.templates.domain.value_objects.template_category import (
    TemplateCategory,
)
from src.modules.templates.domain.value_objects.template_config import TemplateConfig
from src.modules.templates.domain.value_objects.template_status import TemplateStatus
from src.shared.application.dtos import PagedResult
from src.shared.application.ownership import check_ownership, get_or_raise
from src.shared.domain.event_bus import event_bus
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError


class TemplateService:
    """Template 业务服务，编排模板 CRUD、发布、归档用例。"""

    def __init__(
        self,
        template_repo: ITemplateRepository,
    ) -> None:
        self._repo = template_repo

    # -- 模板 CRUD --

    async def create_template(
        self,
        dto: CreateTemplateDTO,
        current_user_id: int,
    ) -> TemplateDTO:
        """创建模板。

        Raises:
            DuplicateTemplateNameError: 名称重复
        """
        await self._check_name_unique(dto.name)

        config = TemplateConfig(
            system_prompt=dto.system_prompt,
            model_id=dto.model_id,
            temperature=dto.temperature,
            max_tokens=dto.max_tokens,
            tool_ids=dto.tool_ids,
            knowledge_base_ids=dto.knowledge_base_ids,
        )
        template = Template(
            name=dto.name,
            description=dto.description,
            category=TemplateCategory(dto.category),
            creator_id=current_user_id,
            config=config,
            tags=dto.tags,
        )
        created = await self._repo.create(template)
        if created.id is None:
            msg = "Template 创建后 ID 不能为空"
            raise ValueError(msg)

        await event_bus.publish_async(
            TemplateCreatedEvent(
                template_id=created.id,
                creator_id=current_user_id,
            ),
        )
        return self._to_dto(created)

    async def get_template(self, template_id: int) -> TemplateDTO:
        """获取模板详情。

        Raises:
            TemplateNotFoundError: 模板不存在
        """
        template = await self._get_or_raise(template_id)
        return self._to_dto(template)

    async def update_template(
        self,
        template_id: int,
        dto: UpdateTemplateDTO,
        current_user_id: int,
    ) -> TemplateDTO:
        """更新模板。仅 DRAFT 状态可更新。

        Raises:
            TemplateNotFoundError, DomainError(FORBIDDEN), InvalidStateTransitionError,
            DuplicateTemplateNameError
        """
        template = await self._get_owned_template(template_id, current_user_id)

        if template.status != TemplateStatus.DRAFT:
            raise InvalidStateTransitionError(
                entity_type="Template",
                current_state=template.status.value,
                target_state="update",
            )

        if dto.name is not None and dto.name != template.name:
            await self._check_name_unique(dto.name)
            template.name = dto.name

        if dto.description is not None:
            template.description = dto.description

        if dto.category is not None:
            template.category = TemplateCategory(dto.category)

        if dto.tags is not None:
            template.tags = dto.tags

        # 重建 TemplateConfig (frozen 值对象, 任一字段变化需整体替换)
        config_overrides: dict[str, str | float | int | list[int]] = {}
        for field in ("system_prompt", "model_id", "temperature", "max_tokens", "tool_ids", "knowledge_base_ids"):
            value = getattr(dto, field)
            if value is not None:
                config_overrides[field] = value

        if config_overrides:
            template.config = replace(template.config, **config_overrides)

        template.touch()
        updated = await self._repo.update(template)
        return self._to_dto(updated)

    async def delete_template(
        self,
        template_id: int,
        current_user_id: int,
    ) -> None:
        """删除模板。仅 DRAFT 状态可物理删除。

        Raises:
            TemplateNotFoundError, DomainError(FORBIDDEN), DomainError(仅 DRAFT)
        """
        template = await self._get_owned_template(template_id, current_user_id)

        if not template.can_delete():
            raise DomainError(
                message="仅 DRAFT 状态的模板可删除",
                code="TEMPLATE_NOT_DELETABLE",
            )

        if template.id is None:
            msg = "Template ID 不能为空"
            raise ValueError(msg)
        await self._repo.delete(template.id)

    # -- 状态转换 --

    async def publish_template(
        self,
        template_id: int,
        current_user_id: int,
    ) -> TemplateDTO:
        """发布模板。DRAFT -> PUBLISHED。

        Raises:
            TemplateNotFoundError, DomainError(FORBIDDEN), InvalidStateTransitionError
        """
        template = await self._get_owned_template(template_id, current_user_id)
        template.publish()
        updated = await self._repo.update(template)

        if updated.id is None:
            msg = "Template 发布后 ID 不能为空"
            raise ValueError(msg)
        await event_bus.publish_async(
            TemplatePublishedEvent(template_id=updated.id),
        )
        return self._to_dto(updated)

    async def archive_template(
        self,
        template_id: int,
        current_user_id: int,
    ) -> TemplateDTO:
        """归档模板。PUBLISHED -> ARCHIVED。

        Raises:
            TemplateNotFoundError, DomainError(FORBIDDEN), InvalidStateTransitionError
        """
        template = await self._get_owned_template(template_id, current_user_id)
        template.archive()
        updated = await self._repo.update(template)

        if updated.id is None:
            msg = "Template 归档后 ID 不能为空"
            raise ValueError(msg)
        await event_bus.publish_async(
            TemplateArchivedEvent(template_id=updated.id),
        )
        return self._to_dto(updated)

    # -- 查询 --

    async def list_templates(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
        tags: list[str] | None = None,
    ) -> PagedResult[TemplateDTO]:
        """查询模板列表。"""
        offset = (page - 1) * page_size
        cat = TemplateCategory(category) if category else None
        kw = keyword or ""

        items, total = await asyncio.gather(
            self._repo.search(kw, category=cat, tags=tags, offset=offset, limit=page_size),
            self._repo.count_by_search(kw, category=cat, tags=tags),
        )

        return PagedResult(
            items=[self._to_dto(t) for t in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def list_my_templates(
        self,
        current_user_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[TemplateDTO]:
        """查询当前用户的模板列表。"""
        offset = (page - 1) * page_size
        items, total = await asyncio.gather(
            self._repo.list_by_creator(current_user_id, offset=offset, limit=page_size),
            self._repo.count_by_creator(current_user_id),
        )

        return PagedResult(
            items=[self._to_dto(t) for t in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    # -- 内部辅助 --

    async def _get_or_raise(self, template_id: int) -> Template:
        return await get_or_raise(self._repo, template_id, TemplateNotFoundError, template_id)

    async def _get_owned_template(self, template_id: int, user_id: int) -> Template:
        """获取模板并校验所有权。"""
        template = await self._get_or_raise(template_id)
        check_ownership(template, user_id, owner_field="creator_id", error_code="FORBIDDEN_TEMPLATE")
        return template

    async def _check_name_unique(self, name: str) -> None:
        existing = await self._repo.get_by_name(name)
        if existing is not None:
            raise DuplicateTemplateNameError(name)

    @staticmethod
    def _to_dto(template: Template) -> TemplateDTO:
        if template.id is None or template.created_at is None or template.updated_at is None:
            msg = "Template 缺少必要字段 (id/created_at/updated_at)"
            raise ValueError(msg)
        return TemplateDTO(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category.value,
            status=template.status.value,
            creator_id=template.creator_id,
            system_prompt=template.config.system_prompt,
            model_id=template.config.model_id,
            temperature=template.config.temperature,
            max_tokens=template.config.max_tokens,
            tool_ids=list(template.config.tool_ids),
            knowledge_base_ids=list(template.config.knowledge_base_ids),
            tags=list(template.tags),
            usage_count=template.usage_count,
            is_featured=template.is_featured,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
