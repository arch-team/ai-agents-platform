"""UsageRecord Repository 集成测试 (SQLite)。"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# 导入 FK 引用的模型，确保 Base.metadata.create_all 能创建所有表
from src.modules.agents.infrastructure.persistence.models.agent_model import AgentModel  # noqa: F401
from src.modules.auth.infrastructure.persistence.models.user_model import UserModel  # noqa: F401
from src.modules.execution.infrastructure.persistence.models.conversation_model import ConversationModel  # noqa: F401
from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.modules.insights.infrastructure.persistence.repositories.usage_record_repository_impl import (
    UsageRecordRepositoryImpl,
)


# -- Fixture --


@pytest.fixture
def session(sqlite_session: AsyncSession) -> AsyncSession:
    return sqlite_session


@pytest.fixture
def repo(session: AsyncSession) -> UsageRecordRepositoryImpl:
    return UsageRecordRepositoryImpl(session=session)


# -- 工厂函数 --


def _make_record(
    user_id: int = 1,
    agent_id: int = 1,
    conversation_id: int | None = 1,
    model_id: str = "anthropic.claude-sonnet-4-20250514",
    tokens_input: int = 1000,
    tokens_output: int = 500,
    estimated_cost: float = 0.0105,
    recorded_at: datetime | None = None,
) -> UsageRecord:
    return UsageRecord(
        user_id=user_id,
        agent_id=agent_id,
        conversation_id=conversation_id,
        model_id=model_id,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        estimated_cost=estimated_cost,
        recorded_at=recorded_at,
    )


# ── CRUD 测试 ──


@pytest.mark.integration
class TestUsageRecordRepositoryCreate:
    """使用记录创建测试。"""

    @pytest.mark.asyncio
    async def test_create_usage_record(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """创建使用记录，验证 id 非空和字段正确。"""
        record = _make_record()
        created = await repo.create(record)
        await session.commit()

        assert created.id is not None
        assert created.user_id == 1
        assert created.agent_id == 1
        assert created.tokens_input == 1000
        assert created.tokens_output == 500
        assert created.estimated_cost == 0.0105

    @pytest.mark.asyncio
    async def test_create_usage_record_without_conversation(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """团队执行场景: conversation_id 为 None 时可正常创建。"""
        record = _make_record(conversation_id=None)
        created = await repo.create(record)
        await session.commit()

        assert created.id is not None
        assert created.conversation_id is None
        assert created.user_id == 1


@pytest.mark.integration
class TestUsageRecordRepositoryGetById:
    """使用记录按 ID 查询测试。"""

    @pytest.mark.asyncio
    async def test_get_by_id(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """创建后按 id 查询，验证返回正确实体。"""
        record = _make_record()
        created = await repo.create(record)
        await session.commit()

        found = await repo.get_by_id(created.id)  # type: ignore[arg-type]
        assert found is not None
        assert found.id == created.id
        assert found.model_id == "anthropic.claude-sonnet-4-20250514"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        repo: UsageRecordRepositoryImpl,
    ) -> None:
        """查询不存在的 id 返回 None。"""
        found = await repo.get_by_id(9999)
        assert found is None


# ── list_by_user 测试 ──


@pytest.mark.integration
class TestUsageRecordRepositoryListByUser:
    """使用记录按用户查询测试。"""

    @pytest.mark.asyncio
    async def test_list_by_user(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """按 user_id 查询，只返回该用户的记录。"""
        target_user = 10
        await repo.create(_make_record(user_id=target_user, conversation_id=1))
        await repo.create(_make_record(user_id=target_user, conversation_id=2))
        await repo.create(_make_record(user_id=99, conversation_id=3))
        await session.commit()

        results = await repo.list_by_user(target_user, offset=0, limit=20)
        assert len(results) == 2
        assert all(r.user_id == target_user for r in results)

    @pytest.mark.asyncio
    async def test_list_by_user_pagination(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """分页参数 offset/limit 正确工作。"""
        user_id = 20
        for i in range(5):
            await repo.create(_make_record(user_id=user_id, conversation_id=i + 1))
        await session.commit()

        page = await repo.list_by_user(user_id, offset=0, limit=2)
        assert len(page) == 2


# ── list_by_agent 测试 ──


@pytest.mark.integration
class TestUsageRecordRepositoryListByAgent:
    """使用记录按 Agent 查询测试。"""

    @pytest.mark.asyncio
    async def test_list_by_agent(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """按 agent_id 查询，只返回该 Agent 的记录。"""
        target_agent = 5
        await repo.create(_make_record(agent_id=target_agent, conversation_id=1))
        await repo.create(_make_record(agent_id=target_agent, conversation_id=2))
        await repo.create(_make_record(agent_id=88, conversation_id=3))
        await session.commit()

        results = await repo.list_by_agent(target_agent, offset=0, limit=20)
        assert len(results) == 2
        assert all(r.agent_id == target_agent for r in results)


# ── list_by_date_range 测试 ──


@pytest.mark.integration
class TestUsageRecordRepositoryListByDateRange:
    """使用记录按日期范围查询测试。"""

    @pytest.mark.asyncio
    async def test_list_by_date_range(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """按日期范围查询，只返回范围内的记录。"""
        base = datetime(2025, 6, 1, tzinfo=UTC)
        await repo.create(_make_record(conversation_id=1, recorded_at=base))
        await repo.create(_make_record(conversation_id=2, recorded_at=base + timedelta(days=1)))
        # 范围外
        await repo.create(_make_record(conversation_id=3, recorded_at=base + timedelta(days=30)))
        await session.commit()

        results = await repo.list_by_date_range(
            start=base - timedelta(hours=1),
            end=base + timedelta(days=2),
        )
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_by_date_range_with_user_filter(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """日期范围 + user_id 过滤。"""
        base = datetime(2025, 6, 1, tzinfo=UTC)
        await repo.create(_make_record(user_id=1, conversation_id=1, recorded_at=base))
        await repo.create(_make_record(user_id=2, conversation_id=2, recorded_at=base))
        await session.commit()

        results = await repo.list_by_date_range(
            start=base - timedelta(hours=1),
            end=base + timedelta(hours=1),
            user_id=1,
        )
        assert len(results) == 1
        assert results[0].user_id == 1


# ── get_aggregated_stats 测试 ──


@pytest.mark.integration
class TestUsageRecordRepositoryAggregatedStats:
    """聚合统计测试。"""

    @pytest.mark.asyncio
    async def test_get_aggregated_stats(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """验证聚合统计返回正确的 total_tokens, total_cost, conversation_count。"""
        await repo.create(_make_record(
            user_id=1, conversation_id=1,
            tokens_input=1000, tokens_output=500, estimated_cost=0.01,
        ))
        await repo.create(_make_record(
            user_id=1, conversation_id=2,
            tokens_input=2000, tokens_output=1000, estimated_cost=0.02,
        ))
        await repo.create(_make_record(
            user_id=1, conversation_id=2,
            tokens_input=500, tokens_output=200, estimated_cost=0.005,
        ))
        await session.commit()

        stats = await repo.get_aggregated_stats(user_id=1)
        assert stats.total_tokens == 5200  # (1000+500) + (2000+1000) + (500+200)
        assert stats.total_cost == pytest.approx(0.035)
        assert stats.conversation_count == 2  # 两个不同的 conversation_id
        assert stats.record_count == 3

    @pytest.mark.asyncio
    async def test_get_aggregated_stats_empty(
        self,
        repo: UsageRecordRepositoryImpl,
    ) -> None:
        """无记录时返回零值。"""
        stats = await repo.get_aggregated_stats()
        assert stats.total_tokens == 0
        assert stats.total_cost == 0.0
        assert stats.conversation_count == 0
        assert stats.record_count == 0

    @pytest.mark.asyncio
    async def test_get_aggregated_stats_with_agent_filter(
        self,
        repo: UsageRecordRepositoryImpl,
        session: AsyncSession,
    ) -> None:
        """按 agent_id 过滤聚合。"""
        await repo.create(_make_record(agent_id=1, conversation_id=1, estimated_cost=0.01))
        await repo.create(_make_record(agent_id=2, conversation_id=2, estimated_cost=0.02))
        await session.commit()

        stats = await repo.get_aggregated_stats(agent_id=1)
        assert stats.record_count == 1
        assert stats.total_cost == pytest.approx(0.01)
