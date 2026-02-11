"""UsageRecord 仓库实现。"""

from datetime import datetime

from sqlalchemy import ColumnElement, distinct, func, select

from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.modules.insights.domain.repositories.usage_record_repository import (
    IUsageRecordRepository,
)
from src.modules.insights.infrastructure.persistence.models.usage_record_model import (
    UsageRecordModel,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class UsageRecordRepositoryImpl(
    PydanticRepository[UsageRecord, UsageRecordModel, int],
    IUsageRecordRepository,
):
    """UsageRecord 仓库的 SQLAlchemy 实现。"""

    entity_class = UsageRecord
    model_class = UsageRecordModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "tokens_input",
            "tokens_output",
            "estimated_cost",
        },
    )

    async def _list_by_field(
        self,
        condition: ColumnElement[bool],
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[UsageRecord]:
        """按条件查询使用记录（按 recorded_at 降序）。"""
        stmt = (
            select(UsageRecordModel)
            .where(condition)
            .offset(offset)
            .limit(limit)
            .order_by(UsageRecordModel.recorded_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[UsageRecord]:
        """按用户查询使用记录（按 recorded_at 降序）。"""
        return await self._list_by_field(
            UsageRecordModel.user_id == user_id,
            offset=offset,
            limit=limit,
        )

    async def list_by_agent(
        self,
        agent_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[UsageRecord]:
        """按 Agent 查询使用记录（按 recorded_at 降序）。"""
        return await self._list_by_field(
            UsageRecordModel.agent_id == agent_id,
            offset=offset,
            limit=limit,
        )

    async def count_by_user(self, user_id: int) -> int:
        """按用户统计使用记录数量。"""
        return await self._count_where(UsageRecordModel.user_id == user_id)

    async def count_by_agent(self, agent_id: int) -> int:
        """按 Agent 统计使用记录数量。"""
        return await self._count_where(UsageRecordModel.agent_id == agent_id)

    async def list_by_date_range(
        self,
        start: datetime,
        end: datetime,
        *,
        user_id: int | None = None,
        agent_id: int | None = None,
    ) -> list[UsageRecord]:
        """按日期范围查询使用记录。"""
        stmt = select(UsageRecordModel).where(
            UsageRecordModel.recorded_at >= start,
            UsageRecordModel.recorded_at <= end,
        )
        if user_id is not None:
            stmt = stmt.where(UsageRecordModel.user_id == user_id)
        if agent_id is not None:
            stmt = stmt.where(UsageRecordModel.agent_id == agent_id)

        stmt = stmt.order_by(UsageRecordModel.recorded_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_aggregated_stats(
        self,
        *,
        user_id: int | None = None,
        agent_id: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[str, float | int]:
        """获取聚合统计数据。"""
        stmt = select(
            func.coalesce(
                func.sum(UsageRecordModel.tokens_input + UsageRecordModel.tokens_output),
                0,
            ).label("total_tokens"),
            func.coalesce(func.sum(UsageRecordModel.estimated_cost), 0.0).label("total_cost"),
            func.count(distinct(UsageRecordModel.conversation_id)).label("conversation_count"),
            func.count().label("record_count"),
        )

        if user_id is not None:
            stmt = stmt.where(UsageRecordModel.user_id == user_id)
        if agent_id is not None:
            stmt = stmt.where(UsageRecordModel.agent_id == agent_id)
        if start is not None:
            stmt = stmt.where(UsageRecordModel.recorded_at >= start)
        if end is not None:
            stmt = stmt.where(UsageRecordModel.recorded_at <= end)

        result = await self._session.execute(stmt)
        row = result.one()
        return {
            "total_tokens": int(row.total_tokens),
            "total_cost": float(row.total_cost),
            "conversation_count": int(row.conversation_count),
            "record_count": int(row.record_count),
        }
