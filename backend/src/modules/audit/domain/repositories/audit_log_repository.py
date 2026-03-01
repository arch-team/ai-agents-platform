"""AuditLog 仓库接口。"""

from abc import abstractmethod
from datetime import datetime

from src.modules.audit.domain.entities.audit_log import AuditAction, AuditCategory, AuditLog
from src.shared.domain.repositories import IRepository


class IAuditLogRepository(IRepository[AuditLog, int]):
    """AuditLog 仓库接口，扩展通用 IRepository 增加审计特有查询。"""

    @abstractmethod
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
    ) -> tuple[list[AuditLog], int]: ...

    @abstractmethod
    async def count_by_category(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]: ...

    @abstractmethod
    async def count_by_action(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]: ...

    @abstractmethod
    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]: ...
