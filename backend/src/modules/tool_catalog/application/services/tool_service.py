"""Tool Catalog 应用服务。"""

import asyncio
from dataclasses import replace

from src.modules.tool_catalog.application.dto.tool_dto import (
    CreateToolDTO,
    PagedToolDTO,
    ToolDTO,
    UpdateToolDTO,
)
from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.events import (
    ToolApprovedEvent,
    ToolCreatedEvent,
    ToolDeletedEvent,
    ToolDeprecatedEvent,
    ToolRejectedEvent,
    ToolSubmittedEvent,
    ToolUpdatedEvent,
)
from src.modules.tool_catalog.domain.exceptions import (
    ToolNameDuplicateError,
    ToolNotFoundError,
)
from src.modules.tool_catalog.domain.repositories.tool_repository import (
    IToolRepository,
)
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.shared.domain.event_bus import event_bus
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError


_EDITABLE_STATUSES: frozenset[ToolStatus] = frozenset({ToolStatus.DRAFT, ToolStatus.REJECTED})


class ToolCatalogService:
    """Tool Catalog 业务服务，编排 Tool 的 CRUD、审批和状态变更用例。"""

    def __init__(self, repository: IToolRepository) -> None:
        self._repository = repository

    # ── CRUD ──

    async def create_tool(self, dto: CreateToolDTO, creator_id: int) -> ToolDTO:
        """创建 Tool（默认 DRAFT）。同 creator 下名称不可重复。

        Raises:
            ToolNameDuplicateError: 名称重复
        """
        await self._check_name_unique(dto.name, creator_id)

        tool = Tool(
            name=dto.name,
            description=dto.description,
            tool_type=dto.tool_type,
            version=dto.version,
            creator_id=creator_id,
            config=ToolConfig(
                server_url=dto.server_url,
                transport=dto.transport,
                endpoint_url=dto.endpoint_url,
                method=dto.method,
                headers=tuple(dto.headers) if dto.headers else (),
                runtime=dto.runtime,
                handler=dto.handler,
                code_uri=dto.code_uri,
                auth_type=dto.auth_type,
                auth_config=tuple(dto.auth_config) if dto.auth_config else (),
            ),
            allowed_roles=tuple(dto.allowed_roles) if dto.allowed_roles else ("admin", "developer"),
        )
        created = await self._repository.create(tool)
        assert created.id is not None
        await event_bus.publish_async(
            ToolCreatedEvent(
                tool_id=created.id,
                creator_id=creator_id,
                name=created.name,
                tool_type=created.tool_type.value,
            ),
        )
        return self._to_dto(created)

    async def get_tool(self, tool_id: int) -> ToolDTO:
        """Raises: ToolNotFoundError"""
        tool = await self._get_tool_or_raise(tool_id)
        return self._to_dto(tool)

    async def get_owned_tool(self, tool_id: int, operator_id: int) -> ToolDTO:
        """获取 Tool 详情（校验所有权）。

        Raises:
            ToolNotFoundError, DomainError(FORBIDDEN_TOOL)
        """
        tool = await self._get_owned_tool(tool_id, operator_id)
        return self._to_dto(tool)

    async def update_tool(
        self,
        tool_id: int,
        dto: UpdateToolDTO,
        operator_id: int,
    ) -> ToolDTO:
        """更新 Tool。仅 creator 可操作，仅 DRAFT/REJECTED 可编辑。

        Raises:
            ToolNotFoundError, DomainError, InvalidStateTransitionError,
            ToolNameDuplicateError
        """
        tool = await self._get_owned_tool(tool_id, operator_id)

        if tool.status not in _EDITABLE_STATUSES:
            raise InvalidStateTransitionError(
                entity_type="Tool",
                current_state=tool.status.value,
                target_state="updated",
            )

        changed_fields: list[str] = []

        # 名称变更需要唯一性校验
        if dto.name is not None and dto.name != tool.name:
            await self._check_name_unique(dto.name, tool.creator_id)
            tool.name = dto.name
            changed_fields.append("name")

        # 普通字段更新
        for field in ("description", "version"):
            value = getattr(dto, field)
            if value is not None:
                setattr(tool, field, value)
                changed_fields.append(field)

        # allowed_roles 更新
        if dto.allowed_roles is not None:
            tool.allowed_roles = tuple(dto.allowed_roles)
            changed_fields.append("allowed_roles")

        # 重建 ToolConfig (frozen 值对象, 任一字段变化需整体替换)
        config_overrides: dict[str, str | tuple[tuple[str, str], ...]] = {}
        for field in (
            "server_url",
            "transport",
            "endpoint_url",
            "method",
            "runtime",
            "handler",
            "code_uri",
            "auth_type",
        ):
            value = getattr(dto, field)
            if value is not None:
                config_overrides[field] = value
                changed_fields.append(field)

        # headers 和 auth_config 需要转换为 tuple
        for field in ("headers", "auth_config"):
            value = getattr(dto, field)
            if value is not None:
                config_overrides[field] = tuple(value)
                changed_fields.append(field)

        if config_overrides:
            tool.config = replace(tool.config, **config_overrides)  # type: ignore[arg-type]

        tool.touch()
        updated = await self._repository.update(tool)

        if changed_fields:
            await event_bus.publish_async(
                ToolUpdatedEvent(
                    tool_id=tool_id,
                    creator_id=updated.creator_id,
                    changed_fields=tuple(changed_fields),
                ),
            )

        return self._to_dto(updated)

    async def delete_tool(self, tool_id: int, operator_id: int) -> None:
        """删除 Tool。仅 DRAFT 可删除。

        Raises:
            ToolNotFoundError, DomainError, InvalidStateTransitionError
        """
        tool = await self._get_owned_tool(tool_id, operator_id)

        if tool.status != ToolStatus.DRAFT:
            raise InvalidStateTransitionError(
                entity_type="Tool",
                current_state=tool.status.value,
                target_state="deleted",
            )

        await self._repository.delete(tool_id)
        await event_bus.publish_async(
            ToolDeletedEvent(tool_id=tool_id, creator_id=tool.creator_id),
        )

    # ── 列表/搜索 ──

    async def list_tools(
        self,
        *,
        creator_id: int | None = None,
        status: ToolStatus | None = None,
        tool_type: ToolType | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedToolDTO:
        """获取 Tool 列表，支持多维筛选和分页。"""
        offset = (page - 1) * page_size

        tools, total = await asyncio.gather(
            self._repository.list_filtered(
                creator_id=creator_id,
                status=status,
                tool_type=tool_type,
                keyword=keyword,
                offset=offset,
                limit=page_size,
            ),
            self._repository.count_filtered(
                creator_id=creator_id,
                status=status,
                tool_type=tool_type,
                keyword=keyword,
            ),
        )

        return PagedToolDTO(
            items=[self._to_dto(t) for t in tools],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def list_approved_tools(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedToolDTO:
        """获取已批准的 Tool 列表（任意认证用户可访问）。"""
        offset = (page - 1) * page_size

        tools, total = await asyncio.gather(
            self._repository.list_approved(offset=offset, limit=page_size),
            self._repository.count_approved(),
        )

        return PagedToolDTO(
            items=[self._to_dto(t) for t in tools],
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── 审批流程 ──

    async def submit_for_review(self, tool_id: int, operator_id: int) -> ToolDTO:
        """提交 Tool 审批。仅 creator 可操作，仅 DRAFT 可提交。

        Raises:
            ToolNotFoundError, DomainError, InvalidStateTransitionError, ValidationError
        """
        tool = await self._get_owned_tool(tool_id, operator_id)
        tool.submit()
        updated = await self._repository.update(tool)
        await event_bus.publish_async(
            ToolSubmittedEvent(
                tool_id=tool_id,
                creator_id=updated.creator_id,
            ),
        )
        return self._to_dto(updated)

    async def approve_tool(self, tool_id: int, reviewer_id: int) -> ToolDTO:
        """审批通过 Tool。仅 PENDING_REVIEW 可审批。

        Raises:
            ToolNotFoundError, InvalidStateTransitionError
        """
        tool = await self._get_tool_or_raise(tool_id)
        tool.approve(reviewer_id)
        updated = await self._repository.update(tool)
        await event_bus.publish_async(
            ToolApprovedEvent(
                tool_id=tool_id,
                creator_id=updated.creator_id,
                reviewer_id=reviewer_id,
            ),
        )
        return self._to_dto(updated)

    async def reject_tool(self, tool_id: int, reviewer_id: int, comment: str) -> ToolDTO:
        """审批拒绝 Tool。仅 PENDING_REVIEW 可拒绝。

        Raises:
            ToolNotFoundError, InvalidStateTransitionError
        """
        tool = await self._get_tool_or_raise(tool_id)
        tool.reject(reviewer_id, comment)
        updated = await self._repository.update(tool)
        await event_bus.publish_async(
            ToolRejectedEvent(
                tool_id=tool_id,
                creator_id=updated.creator_id,
                reviewer_id=reviewer_id,
                comment=comment,
            ),
        )
        return self._to_dto(updated)

    # ── 状态变更 ──

    async def deprecate_tool(self, tool_id: int, operator_id: int) -> ToolDTO:
        """废弃 Tool。creator 或 ADMIN 可操作（ADMIN 权限在 API 层校验）。

        Raises:
            ToolNotFoundError, DomainError, InvalidStateTransitionError
        """
        tool = await self._get_owned_tool(tool_id, operator_id)
        tool.deprecate()
        updated = await self._repository.update(tool)
        await event_bus.publish_async(
            ToolDeprecatedEvent(
                tool_id=tool_id,
                creator_id=updated.creator_id,
            ),
        )
        return self._to_dto(updated)

    # ── 内部辅助方法 ──

    async def _get_tool_or_raise(self, tool_id: int) -> Tool:
        tool = await self._repository.get_by_id(tool_id)
        if tool is None:
            raise ToolNotFoundError(tool_id)
        return tool

    async def _get_owned_tool(self, tool_id: int, operator_id: int) -> Tool:
        tool = await self._get_tool_or_raise(tool_id)
        if tool.creator_id != operator_id:
            raise DomainError(
                message="无权操作此 Tool",
                code="FORBIDDEN_TOOL",
            )
        return tool

    async def _check_name_unique(self, name: str, creator_id: int) -> None:
        existing = await self._repository.get_by_name_and_creator(name, creator_id)
        if existing is not None:
            raise ToolNameDuplicateError(name, creator_id)

    @staticmethod
    def _to_dto(tool: Tool) -> ToolDTO:
        assert tool.id is not None
        assert tool.created_at is not None
        assert tool.updated_at is not None
        return ToolDTO(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            tool_type=tool.tool_type.value,
            version=tool.version,
            status=tool.status.value,
            creator_id=tool.creator_id,
            server_url=tool.config.server_url,
            transport=tool.config.transport,
            endpoint_url=tool.config.endpoint_url,
            method=tool.config.method,
            headers=list(tool.config.headers),
            runtime=tool.config.runtime,
            handler=tool.config.handler,
            code_uri=tool.config.code_uri,
            auth_type=tool.config.auth_type,
            auth_config=list(tool.config.auth_config),
            allowed_roles=list(tool.allowed_roles),
            reviewer_id=tool.reviewer_id,
            review_comment=tool.review_comment,
            reviewed_at=tool.reviewed_at,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
        )
