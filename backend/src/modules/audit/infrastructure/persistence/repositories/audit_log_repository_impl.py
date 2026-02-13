"""AuditLog 仓库实现。"""

from datetime import datetime

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import InstrumentedAttribute

from src.modules.audit.domain.entities.audit_log import AuditAction, AuditCategory, AuditLog
from src.modules.audit.domain.repositories.audit_log_repository import IAuditLogRepository
from src.modules.audit.infrastructure.persistence.models.audit_log_model import AuditLogModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class AuditLogRepositoryImpl(
    PydanticRepository[AuditLog, AuditLogModel, int],
    IAuditLogRepository,
):
    """AuditLog 仓库的 SQLAlchemy 实现。"""

    entity_class = AuditLog
    model_class = AuditLogModel
    # append-only: 不支持更新
    _updatable_fields: frozenset[str] = frozenset()

    def _to_entity(self, model: AuditLogModel) -> AuditLog:
        return AuditLog(
            id=model.id,
            actor_id=model.actor_id,
            actor_name=model.actor_name,
            action=AuditAction(model.action),
            category=AuditCategory(model.category),
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            resource_name=model.resource_name,
            module=model.module,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            request_method=model.request_method,
            request_path=model.request_path,
            status_code=model.status_code,
            result=model.result,
            error_message=model.error_message,
            details=model.details,
            occurred_at=model.occurred_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: AuditLog) -> AuditLogModel:
        return AuditLogModel(
            id=entity.id,
            actor_id=entity.actor_id,
            actor_name=entity.actor_name,
            action=entity.action.value,
            category=entity.category.value,
            resource_type=entity.resource_type,
            resource_id=entity.resource_id,
            resource_name=entity.resource_name,
            module=entity.module,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
            request_method=entity.request_method,
            request_path=entity.request_path,
            status_code=entity.status_code,
            result=entity.result,
            error_message=entity.error_message,
            details=entity.details,
            occurred_at=entity.occurred_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    # ── 查询辅助方法 ──

    @staticmethod
    def _build_filters(
        *,
        category: AuditCategory | None = None,
        action: AuditAction | None = None,
        actor_id: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[ColumnElement[bool]]:
        """构建查询条件列表。"""
        filters: list[ColumnElement[bool]] = []
        if category is not None:
            filters.append(AuditLogModel.category == category.value)
        if action is not None:
            filters.append(AuditLogModel.action == action.value)
        if actor_id is not None:
            filters.append(AuditLogModel.actor_id == actor_id)
        if resource_type is not None:
            filters.append(AuditLogModel.resource_type == resource_type)
        if resource_id is not None:
            filters.append(AuditLogModel.resource_id == resource_id)
        if start_date is not None:
            filters.append(AuditLogModel.occurred_at >= start_date)
        if end_date is not None:
            filters.append(AuditLogModel.occurred_at <= end_date)
        return filters

    # ── 接口实现 ──

    async def list_filtered(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        category: AuditCategory | None = None,
        action: AuditAction | None = None,
        actor_id: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        """分页筛选审计日志。"""
        filters = self._build_filters(
            category=category,
            action=action,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
        )
        offset = (page - 1) * page_size
        return await self._list_and_count(*filters, offset=offset, limit=page_size)

    async def _count_grouped_by(
        self,
        column: InstrumentedAttribute[str] | ColumnElement[str],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        """按指定列分组统计审计日志数量。"""
        filters: list[ColumnElement[bool]] = []
        if start_date is not None:
            filters.append(AuditLogModel.occurred_at >= start_date)
        if end_date is not None:
            filters.append(AuditLogModel.occurred_at <= end_date)

        stmt = select(column, func.count()).where(*filters).group_by(column)
        result = await self._session.execute(stmt)
        return dict(result.all())  # type: ignore[arg-type]

    async def count_by_category(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        """按分类统计审计日志数量。"""
        return await self._count_grouped_by(AuditLogModel.category, start_date, end_date)

    async def count_by_action(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        """按操作类型统计审计日志数量。"""
        return await self._count_grouped_by(AuditLogModel.action, start_date, end_date)

    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        """按资源查询审计日志。"""
        filters = [
            AuditLogModel.resource_type == resource_type,
            AuditLogModel.resource_id == resource_id,
        ]
        offset = (page - 1) * page_size
        return await self._list_and_count(*filters, offset=offset, limit=page_size)

    # ── append-only: 禁止更新和删除 ──

    async def update(self, entity: AuditLog) -> AuditLog:  # noqa: ARG002
        """审计日志不支持更新。

        Raises:
            NotImplementedError: 审计日志是 append-only
        """
        msg = "audit log is append-only, update not supported"
        raise NotImplementedError(msg)

    async def delete(self, entity_id: int) -> None:  # noqa: ARG002
        """审计日志不支持删除。

        Raises:
            NotImplementedError: 审计日志是 append-only
        """
        msg = "audit log is append-only, delete not supported"
        raise NotImplementedError(msg)
