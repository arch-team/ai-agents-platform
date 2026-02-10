"""Tool 仓库实现。"""

import json
from collections.abc import Sequence

from sqlalchemy import ColumnElement, select

from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.repositories.tool_repository import IToolRepository
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.modules.tool_catalog.infrastructure.persistence.models.tool_model import ToolModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


def _serialize_tuple_pairs(pairs: tuple[tuple[str, str], ...]) -> str:
    """将 tuple[tuple[str, str], ...] 序列化为 JSON 字符串。"""
    return json.dumps([list(p) for p in pairs]) if pairs else ""


def _deserialize_tuple_pairs(raw: str) -> tuple[tuple[str, str], ...]:
    """将 JSON 字符串反序列化为 tuple[tuple[str, str], ...]。"""
    return tuple(tuple(p) for p in json.loads(raw)) if raw else ()


def _serialize_roles(roles: tuple[str, ...]) -> str:
    """将 allowed_roles 序列化为 JSON 字符串。"""
    return json.dumps(list(roles))


def _deserialize_roles(raw: str) -> tuple[str, ...]:
    """将 JSON 字符串反序列化为 allowed_roles。"""
    return tuple(json.loads(raw)) if raw else ("admin", "developer")


class ToolRepositoryImpl(PydanticRepository[Tool, ToolModel, int], IToolRepository):
    """Tool 仓库的 SQLAlchemy 实现。"""

    entity_class = Tool
    model_class = ToolModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "name",
            "description",
            "version",
            "status",
            "server_url",
            "transport",
            "endpoint_url",
            "method",
            "headers",
            "runtime",
            "handler",
            "code_uri",
            "auth_type",
            "auth_config",
            "allowed_roles",
            "reviewer_id",
            "review_comment",
            "reviewed_at",
        },
    )

    def _to_entity(self, model: ToolModel) -> Tool:
        return Tool(
            id=model.id,
            name=model.name,
            description=model.description,
            tool_type=ToolType(model.tool_type),
            version=model.version,
            status=ToolStatus(model.status),
            creator_id=model.creator_id,
            config=ToolConfig(
                server_url=model.server_url,
                transport=model.transport,
                endpoint_url=model.endpoint_url,
                method=model.method,
                headers=_deserialize_tuple_pairs(model.headers),
                runtime=model.runtime,
                handler=model.handler,
                code_uri=model.code_uri,
                auth_type=model.auth_type,
                auth_config=_deserialize_tuple_pairs(model.auth_config),
            ),
            allowed_roles=_deserialize_roles(model.allowed_roles),
            reviewer_id=model.reviewer_id,
            review_comment=model.review_comment,
            reviewed_at=model.reviewed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _flatten_config(self, entity: Tool) -> dict[str, object]:
        """将 Entity 的 config 和扁平字段展开为 Model 列数据。"""
        return {
            "name": entity.name,
            "description": entity.description,
            "version": entity.version,
            "status": entity.status.value,
            "server_url": entity.config.server_url,
            "transport": entity.config.transport,
            "endpoint_url": entity.config.endpoint_url,
            "method": entity.config.method,
            "headers": _serialize_tuple_pairs(entity.config.headers),
            "runtime": entity.config.runtime,
            "handler": entity.config.handler,
            "code_uri": entity.config.code_uri,
            "auth_type": entity.config.auth_type,
            "auth_config": _serialize_tuple_pairs(entity.config.auth_config),
            "allowed_roles": _serialize_roles(entity.allowed_roles),
            "reviewer_id": entity.reviewer_id,
            "review_comment": entity.review_comment,
            "reviewed_at": entity.reviewed_at,
        }

    def _to_model(self, entity: Tool) -> ToolModel:
        return ToolModel(
            id=entity.id,
            tool_type=entity.tool_type.value,
            creator_id=entity.creator_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            **self._flatten_config(entity),
        )

    def _get_update_data(self, entity: Tool) -> dict[str, object]:
        return self._flatten_config(entity)

    # -- 查询辅助方法 --

    @staticmethod
    def _build_filters(
        *,
        status: ToolStatus | None = None,
        tool_type: ToolType | None = None,
        keyword: str | None = None,
        creator_id: int | None = None,
    ) -> Sequence[ColumnElement[bool]]:
        """动态构建 WHERE 条件。"""
        filters: list[ColumnElement[bool]] = []
        if status is not None:
            filters.append(ToolModel.status == status.value)
        if tool_type is not None:
            filters.append(ToolModel.tool_type == tool_type.value)
        if keyword is not None:
            filters.append(ToolModel.name.ilike(f"%{keyword}%"))
        if creator_id is not None:
            filters.append(ToolModel.creator_id == creator_id)
        return filters

    # -- 接口实现 --

    async def list_by_creator(  # noqa: D102
        self,
        creator_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Tool]:
        return await self._list_where(
            ToolModel.creator_id == creator_id,
            offset=offset,
            limit=limit,
        )

    async def count_by_creator(self, creator_id: int) -> int:  # noqa: D102
        return await self._count_where(ToolModel.creator_id == creator_id)

    async def get_by_name_and_creator(  # noqa: D102
        self,
        name: str,
        creator_id: int,
    ) -> Tool | None:
        stmt = select(ToolModel).where(
            ToolModel.name == name,
            ToolModel.creator_id == creator_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_approved(  # noqa: D102
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Tool]:
        return await self._list_where(
            ToolModel.status == ToolStatus.APPROVED.value,
            offset=offset,
            limit=limit,
        )

    async def count_approved(self) -> int:  # noqa: D102
        return await self._count_where(ToolModel.status == ToolStatus.APPROVED.value)

    async def list_filtered(  # noqa: D102
        self,
        *,
        status: ToolStatus | None = None,
        tool_type: ToolType | None = None,
        keyword: str | None = None,
        creator_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Tool]:
        filters = self._build_filters(
            status=status,
            tool_type=tool_type,
            keyword=keyword,
            creator_id=creator_id,
        )
        return await self._list_where(*filters, offset=offset, limit=limit)

    async def count_filtered(  # noqa: D102
        self,
        *,
        status: ToolStatus | None = None,
        tool_type: ToolType | None = None,
        keyword: str | None = None,
        creator_id: int | None = None,
    ) -> int:
        filters = self._build_filters(
            status=status,
            tool_type=tool_type,
            keyword=keyword,
            creator_id=creator_id,
        )
        return await self._count_where(*filters)
