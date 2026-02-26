"""AgentQuerierImpl TTL 缓存测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.agents.domain import Agent, AgentConfig, AgentStatus, IAgentRepository
from src.modules.agents.infrastructure import AgentQuerierImpl


def _make_agent(
    *, status: AgentStatus = AgentStatus.ACTIVE, agent_id: int = 1,
) -> Agent:
    return Agent(
        id=agent_id,
        name="Test Agent",
        description="Test",
        system_prompt="You are helpful.",
        status=status,
        owner_id=1,
        config=AgentConfig(
            model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
        ),
    )


@pytest.mark.unit
class TestAgentQuerierCache:
    """AgentQuerierImpl TTL 缓存测试。"""

    @pytest.mark.asyncio
    async def test_consecutive_queries_hit_cache(self) -> None:
        """同一 Agent 连续 10 次查询只产生 1 次 repo 调用。"""
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent()
        querier = AgentQuerierImpl(agent_repository=repo)

        for _ in range(10):
            result = await querier.get_active_agent(1)
            assert result is not None

        repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_different_agents_separate_cache_entries(self) -> None:
        """不同 Agent ID 应分别缓存。"""
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.side_effect = lambda aid: _make_agent(agent_id=aid)
        querier = AgentQuerierImpl(agent_repository=repo)

        result1 = await querier.get_active_agent(1)
        result2 = await querier.get_active_agent(2)

        assert result1 is not None
        assert result2 is not None
        assert result1.id == 1
        assert result2.id == 2
        assert repo.get_by_id.call_count == 2

    @pytest.mark.asyncio
    async def test_none_result_is_cached(self) -> None:
        """Agent 不存在时 None 结果也应被缓存。"""
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = None
        querier = AgentQuerierImpl(agent_repository=repo)

        for _ in range(5):
            result = await querier.get_active_agent(999)
            assert result is None

        repo.get_by_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_cache_invalidation_after_clear(self) -> None:
        """清除缓存后应重新查询 repo。"""
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent()
        querier = AgentQuerierImpl(agent_repository=repo)

        await querier.get_active_agent(1)
        assert repo.get_by_id.call_count == 1

        querier.clear_cache()

        await querier.get_active_agent(1)
        assert repo.get_by_id.call_count == 2

    @pytest.mark.asyncio
    async def test_non_active_agent_cached_as_none(self) -> None:
        """非 ACTIVE 状态的 Agent 缓存为 None。"""
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent(status=AgentStatus.DRAFT)
        querier = AgentQuerierImpl(agent_repository=repo)

        result1 = await querier.get_active_agent(1)
        result2 = await querier.get_active_agent(1)

        assert result1 is None
        assert result2 is None
        repo.get_by_id.assert_called_once()
