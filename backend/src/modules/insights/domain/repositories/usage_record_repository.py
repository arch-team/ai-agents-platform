"""使用记录仓库接口。"""

from abc import abstractmethod
from datetime import datetime

from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.shared.domain.repositories import IRepository


class IUsageRecordRepository(IRepository[UsageRecord, int]):
    """使用记录仓库接口。"""

    @abstractmethod
    async def list_by_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[UsageRecord]:
        """按用户查询使用记录列表。"""

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[UsageRecord]:
        """按 Agent 查询使用记录列表。"""

    @abstractmethod
    async def list_by_date_range(
        self,
        start: datetime,
        end: datetime,
        *,
        user_id: int | None = None,
        agent_id: int | None = None,
    ) -> list[UsageRecord]:
        """按日期范围查询使用记录。"""

    @abstractmethod
    async def get_aggregated_stats(
        self,
        *,
        user_id: int | None = None,
        agent_id: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[str, float | int]:
        """获取聚合统计数据（总 token、总 cost、对话数）。"""
