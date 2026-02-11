"""Insights 应用服务。"""

from datetime import datetime

from src.modules.insights.application.dto.insights_dto import (
    CreateUsageRecordDTO,
    PagedUsageRecordDTO,
    UsageRecordDTO,
    UsageSummaryDTO,
)
from src.modules.insights.application.interfaces.cost_calculator import (
    ICostCalculator,
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
from src.shared.domain.event_bus import event_bus


class InsightsService:
    """Insights 业务服务, 编排使用记录和成本分析用例。"""

    def __init__(
        self,
        usage_repo: IUsageRecordRepository,
        cost_calculator: ICostCalculator,
    ) -> None:
        self._usage_repo = usage_repo
        self._cost_calculator = cost_calculator

    async def record_usage(self, dto: CreateUsageRecordDTO) -> UsageRecordDTO:
        """创建使用记录并计算成本。"""
        breakdown = self._cost_calculator.calculate_cost(
            dto.model_id,
            dto.tokens_input,
            dto.tokens_output,
        )

        record = UsageRecord(
            user_id=dto.user_id,
            agent_id=dto.agent_id,
            conversation_id=dto.conversation_id,
            model_id=dto.model_id,
            tokens_input=dto.tokens_input,
            tokens_output=dto.tokens_output,
            estimated_cost=breakdown.total_cost,
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
                estimated_cost=breakdown.total_cost,
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
    ) -> PagedUsageRecordDTO:
        """获取使用记录列表 (按用户或 Agent 过滤)。"""
        offset = (page - 1) * page_size

        if user_id is not None:
            items = await self._usage_repo.list_by_user(
                user_id,
                offset=offset,
                limit=page_size,
            )
            total = await self._usage_repo.count_by_user(user_id)
        elif agent_id is not None:
            items = await self._usage_repo.list_by_agent(
                agent_id,
                offset=offset,
                limit=page_size,
            )
            total = await self._usage_repo.count_by_agent(agent_id)
        else:
            items = await self._usage_repo.list(offset=offset, limit=page_size)
            total = await self._usage_repo.count()

        return PagedUsageRecordDTO(
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
            total_tokens=int(stats["total_tokens"]),
            total_cost=float(stats["total_cost"]),
            conversation_count=int(stats["conversation_count"]),
            record_count=int(stats["record_count"]),
            period=period,
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
