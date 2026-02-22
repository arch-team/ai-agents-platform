"""AuditService 应用服务。"""

from datetime import datetime

from src.modules.audit.application.dto.audit_log_dto import (
    AuditLogDTO,
    AuditStatsDTO,
    CreateAuditLogDTO,
)
from src.modules.audit.domain.entities.audit_log import AuditAction, AuditCategory, AuditLog
from src.modules.audit.domain.events import AuditLogCreatedEvent
from src.modules.audit.domain.exceptions import AuditNotFoundError
from src.modules.audit.domain.repositories.audit_log_repository import IAuditLogRepository
from src.shared.application.dtos import PagedResult
from src.shared.domain.base_entity import utc_now
from src.shared.domain.event_bus import event_bus


class AuditService:
    """审计业务服务，编排审计日志的记录和查询用例。"""

    def __init__(self, repository: IAuditLogRepository) -> None:
        self._repository = repository

    @staticmethod
    def _to_dto(entity: AuditLog) -> AuditLogDTO:
        """将 AuditLog 实体转换为 DTO。"""
        return AuditLogDTO(
            id=entity.id,  # type: ignore[arg-type]
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
            created_at=entity.created_at,  # type: ignore[arg-type]
            updated_at=entity.updated_at,  # type: ignore[arg-type]
        )

    async def record(self, dto: CreateAuditLogDTO) -> AuditLogDTO:
        """记录审计日志。"""
        entity = AuditLog(
            actor_id=dto.actor_id,
            actor_name=dto.actor_name,
            action=AuditAction(dto.action),
            category=AuditCategory(dto.category),
            resource_type=dto.resource_type,
            resource_id=dto.resource_id,
            resource_name=dto.resource_name,
            module=dto.module,
            ip_address=dto.ip_address,
            user_agent=dto.user_agent,
            request_method=dto.request_method,
            request_path=dto.request_path,
            status_code=dto.status_code,
            result=dto.result,
            error_message=dto.error_message,
            details=dto.details,
            occurred_at=dto.occurred_at or utc_now(),
        )
        saved = await self._repository.create(entity)

        await event_bus.publish_async(
            AuditLogCreatedEvent(
                audit_log_id=saved.id,  # type: ignore[arg-type]
                action=saved.action.value,
                category=saved.category.value,
                actor_id=saved.actor_id,
            ),
        )

        return self._to_dto(saved)

    async def get_by_id(self, audit_log_id: int) -> AuditLogDTO:
        """获取单条审计日志。

        Raises:
            AuditNotFoundError: 审计记录不存在
        """
        entity = await self._repository.get_by_id(audit_log_id)
        if entity is None:
            raise AuditNotFoundError(audit_log_id)
        return self._to_dto(entity)

    async def list_filtered(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        action: str | None = None,
        actor_id: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> PagedResult[AuditLogDTO]:
        """分页筛选审计日志。"""
        items, total = await self._repository.list_filtered(
            page=page,
            page_size=page_size,
            category=AuditCategory(category) if category else None,
            action=AuditAction(action) if action else None,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
        )
        return PagedResult(
            items=[self._to_dto(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> AuditStatsDTO:
        """获取审计统计信息。"""
        # SQLAlchemy AsyncSession 不支持同一 session 的并发操作, 必须顺序执行
        by_category = await self._repository.count_by_category(start_date, end_date)
        by_action = await self._repository.count_by_action(start_date, end_date)
        total = sum(by_category.values())
        return AuditStatsDTO(
            by_category=by_category,
            by_action=by_action,
            total=total,
        )

    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[AuditLogDTO]:
        """按资源查询审计日志。"""
        items, total = await self._repository.get_by_resource(
            resource_type,
            resource_id,
            page=page,
            page_size=page_size,
        )
        return PagedResult(
            items=[self._to_dto(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
