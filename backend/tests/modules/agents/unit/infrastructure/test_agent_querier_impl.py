"""AgentQuerierImpl 单元测试。"""

import pytest
from unittest.mock import AsyncMock

from src.modules.agents.domain import Agent, AgentConfig, AgentStatus, IAgentRepository
from src.modules.agents.infrastructure import AgentQuerierImpl
from src.shared.domain import ActiveAgentInfo, IAgentQuerier


def _make_agent(
    *, status: AgentStatus = AgentStatus.ACTIVE, agent_id: int = 1
) -> Agent:
    return Agent(
        id=agent_id,
        name="Test Agent",
        description="Test",
        system_prompt="You are helpful.",
        status=status,
        owner_id=1,
        config=AgentConfig(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
        ),
    )


@pytest.mark.unit
class TestAgentQuerierImpl:
    """AgentQuerierImpl 单元测试。"""

    def test_implements_interface(self) -> None:
        assert issubclass(AgentQuerierImpl, IAgentQuerier)

    @pytest.mark.asyncio
    async def test_get_active_agent_success(self) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent()
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_active_agent(1)

        assert result is not None
        assert isinstance(result, ActiveAgentInfo)
        assert result.id == 1
        assert result.system_prompt == "You are helpful."
        assert result.model_id == "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    @pytest.mark.asyncio
    async def test_get_active_agent_not_found(self) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = None
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_active_agent(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_agent_not_active_draft(self) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent(status=AgentStatus.DRAFT)
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_active_agent(1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_agent_not_active_archived(self) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent(status=AgentStatus.ARCHIVED)
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_active_agent(1)

        assert result is None

    @pytest.mark.asyncio
    async def test_converts_config_fields(self) -> None:
        agent = _make_agent()
        agent.config = AgentConfig(
            model_id="custom-model",
            temperature=0.5,
            max_tokens=1024,
            top_p=0.9,
            stop_sequences=("stop1", "stop2"),
        )
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = agent
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_active_agent(1)

        assert result is not None
        assert result.model_id == "custom-model"
        assert result.temperature == 0.5
        assert result.max_tokens == 1024
        assert result.top_p == 0.9
        assert result.stop_sequences == ("stop1", "stop2")
        assert result.runtime_type == "agent"

    @pytest.mark.asyncio
    async def test_maps_runtime_type(self) -> None:
        agent = _make_agent()
        agent.config = AgentConfig(runtime_type="basic")
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = agent
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_active_agent(1)

        assert result is not None
        assert result.runtime_type == "basic"
