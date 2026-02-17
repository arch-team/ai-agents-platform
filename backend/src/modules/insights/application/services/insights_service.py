"""Insights 应用服务。"""

from datetime import datetime

from src.modules.insights.application.dto.insights_dto import (
    CreateUsageRecordDTO,
    InsightsSummaryDTO,
    UsageRecordDTO,
    UsageSummaryDTO,
)
from src.modules.insights.application.interfaces.cost_explorer import (
    ICostExplorer,
)
from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.modules.insights.domain.events import UsageRecordCreatedEvent
from src.modules.insights.domain.exceptions import (
    InvalidDateRangeError,
    UsageRecordNotFoundError,
)
from src.modules.insights.domain.repositories.usage_record_repository import (
    IUsageRecordRepository,
)
from src.modules.insights.domain.value_objects.agent_token_breakdown import (
    AgentTokenBreakdown,
)
from src.modules.insights.domain.value_objects.daily_usage_trend import (
    DailyUsageTrend,
)
from src.shared.application.dtos import PagedResult
from src.shared.domain.event_bus import event_bus


class InsightsService:
    """Insights 业务服务, 编排使用记录和成本分析用例。"""

    def __init__(
        self,
        usage_repo: IUsageRecordRepository,
        cost_explorer: ICostExplorer | None = None,
    ) -> None:
        self._usage_repo = usage_repo
        self._cost_explorer = cost_explorer

    async def record_usage(self, dto: CreateUsageRecordDTO) -> UsageRecordDTO:
        """创建使用记录。

        成本估算已弃用 — 平台总成本由 AWS Cost Explorer 提供真实账单，
        estimated_cost 固定为 0.0。
        """
        record = UsageRecord(
            user_id=dto.user_id,
            agent_id=dto.agent_id,
            conversation_id=dto.conversation_id,
            model_id=dto.model_id,
            tokens_input=dto.tokens_input,
            tokens_output=dto.tokens_output,
            estimated_cost=0.0,
        )

        created = await self._usage_repo.create(record)
        if created.id is None:
            msg = "UsageRecord 创建后 ID 不能为空"
            raise ValueError(msg)

        await event_bus.publish_async(
            UsageRecordCreatedEvent(
                record_id=created.id,
                user_id=dto.user_id,
                agent_id=dto.agent_id,
                estimated_cost=0.0,
            ),
        )

        return self._to_dto(created)

    async def get_usage_record(self, record_id: int) -> UsageRecordDTO:
        """获取单条使用记录。

        Raises:
            UsageRecordNotFoundError: 记录不存在
        """
        record = await self._usage_repo.get_by_id(record_id)
        if record is None:
            raise UsageRecordNotFoundError(record_id)
        return self._to_dto(record)

    async def list_usage_records(
        self,
        *,
        user_id: int | None = None,
        agent_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[UsageRecordDTO]:
        """获取使用记录列表 (按用户或 Agent 过滤)。"""
        offset = (page - 1) * page_size

        if user_id is not None:
            items = await self._usage_repo.list_by_user(user_id, offset=offset, limit=page_size)
            total = await self._usage_repo.count_by_user(user_id)
        elif agent_id is not None:
            items = await self._usage_repo.list_by_agent(agent_id, offset=offset, limit=page_size)
            total = await self._usage_repo.count_by_agent(agent_id)
        else:
            items = await self._usage_repo.list(offset=offset, limit=page_size)
            total = await self._usage_repo.count()

        return PagedResult(
            items=[self._to_dto(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_usage_summary(
        self,
        *,
        user_id: int | None = None,
        agent_id: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        period: str = "all",
    ) -> UsageSummaryDTO:
        """获取使用量摘要统计。

        Raises:
            InvalidDateRangeError: start > end
        """
        if start is not None and end is not None and start > end:
            raise InvalidDateRangeError

        stats = await self._usage_repo.get_aggregated_stats(
            user_id=user_id,
            agent_id=agent_id,
            start=start,
            end=end,
        )

        return UsageSummaryDTO(
            total_tokens=stats.total_tokens,
            total_cost=stats.total_cost,
            conversation_count=stats.conversation_count,
            record_count=stats.record_count,
            period=period,
        )

    async def get_cost_breakdown(
        self,
        start: datetime,
        end: datetime,
    ) -> list[AgentTokenBreakdown]:
        """获取按 Agent 维度的 Token 消耗归因。"""
        if start > end:
            raise InvalidDateRangeError
        return await self._usage_repo.get_cost_breakdown_by_agent(start=start, end=end)

    async def get_usage_trends(
        self,
        start: datetime,
        end: datetime,
    ) -> list[DailyUsageTrend]:
        """获取按日维度的使用趋势。"""
        if start > end:
            raise InvalidDateRangeError
        return await self._usage_repo.get_daily_usage_trends(start=start, end=end)

    async def get_insights_summary(
        self,
        start: datetime,
        end: datetime,
    ) -> InsightsSummaryDTO:
        """获取 Insights 概览 — 组合 Cost Explorer + Repository 聚合。"""
        if start > end:
            raise InvalidDateRangeError

        # Repository 聚合
        stats = await self._usage_repo.get_aggregated_stats(start=start, end=end)

        # Cost Explorer 真实成本 (降级为 0.0)
        total_cost = 0.0
        if self._cost_explorer is not None:
            cost_summary = await self._cost_explorer.get_bedrock_cost(
                start_date=start.strftime("%Y-%m-%d"),
                end_date=end.strftime("%Y-%m-%d"),
            )
            total_cost = cost_summary.total_cost

        # Agent 计数从 UsageRecord 中近似获取
        distinct_agents = await self._usage_repo.count_distinct_agents(start=start, end=end)

        return InsightsSummaryDTO(
            total_agents=distinct_agents,
            active_agents=distinct_agents,
            total_invocations=stats.record_count,
            total_cost=total_cost,
            total_tokens=stats.total_tokens,
        )

    @staticmethod
    def _to_dto(record: UsageRecord) -> UsageRecordDTO:
        if record.id is None or record.created_at is None or record.recorded_at is None:
            msg = "UsageRecord 缺少必要字段 (id/created_at/recorded_at)"
            raise ValueError(msg)
        return UsageRecordDTO(
            id=record.id,
            user_id=record.user_id,
            agent_id=record.agent_id,
            conversation_id=record.conversation_id,
            model_id=record.model_id,
            tokens_input=record.tokens_input,
            tokens_output=record.tokens_output,
            estimated_cost=record.estimated_cost,
            recorded_at=record.recorded_at,
            created_at=record.created_at,
        )
