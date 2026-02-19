"""使用记录仓库接口。"""

from abc import abstractmethod
from datetime import datetime

from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.modules.insights.domain.value_objects.agent_token_breakdown import (
    AgentTokenBreakdown,
)
from src.modules.insights.domain.value_objects.aggregated_stats import AggregatedStats
from src.modules.insights.domain.value_objects.daily_usage_trend import (
    DailyUsageTrend,
)
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
    async def count_by_user(self, user_id: int) -> int:
        """按用户统计使用记录数量。"""

    @abstractmethod
    async def count_by_agent(self, agent_id: int) -> int:
        """按 Agent 统计使用记录数量。"""

    @abstractmethod
    async def get_aggregated_stats(
        self,
        *,
        user_id: int | None = None,
        agent_id: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> AggregatedStats:
        """获取聚合统计数据（总 token、总 cost、对话数）。"""

    @abstractmethod
    async def get_cost_breakdown_by_agent(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[AgentTokenBreakdown]:
        """按 Agent 维度聚合 Token 消耗。"""

    @abstractmethod
    async def get_daily_usage_trends(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[DailyUsageTrend]:
        """按日维度聚合使用趋势。"""

    @abstractmethod
    async def count_distinct_agents(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> int:
        """统计日期范围内的不重复 Agent 数。"""
