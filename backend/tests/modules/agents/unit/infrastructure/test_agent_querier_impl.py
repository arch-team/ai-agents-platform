"""AgentQuerierImpl 单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.agents.domain import Agent, AgentConfig, AgentStatus, IAgentRepository
from src.modules.agents.infrastructure import AgentQuerierImpl
from src.shared.domain import ActiveAgentInfo, IAgentQuerier
from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45


def _make_agent(
    *,
    status: AgentStatus = AgentStatus.ACTIVE,
    agent_id: int = 1,
) -> Agent:
    return Agent(
        id=agent_id,
        name="Test Agent",
        description="Test",
        system_prompt="You are helpful.",
        status=status,
        owner_id=1,
        config=AgentConfig(
            model_id=MODEL_CLAUDE_HAIKU_45,
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
    async def test_get_executable_agent_success(self) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent()
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert isinstance(result, ActiveAgentInfo)
        assert result.id == 1
        assert result.system_prompt == "You are helpful."
        assert result.model_id == MODEL_CLAUDE_HAIKU_45

    @pytest.mark.asyncio
    async def test_get_executable_agent_not_found(self) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = None
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_executable_agent_not_active_draft(self) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent(status=AgentStatus.DRAFT)
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_executable_agent_not_active_archived(self) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent(status=AgentStatus.ARCHIVED)
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

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

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert result.model_id == "custom-model"
        assert result.temperature == 0.5
        assert result.max_tokens == 1024
        assert result.top_p == 0.9
        assert result.stop_sequences == ("stop1", "stop2")
        assert result.runtime_type == "agent"

    @pytest.mark.asyncio
    async def test_maps_tool_ids(self) -> None:
        agent = _make_agent()
        agent.config = AgentConfig(tool_ids=(10, 20, 30))
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = agent
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert result.tool_ids == (10, 20, 30)

    @pytest.mark.asyncio
    async def test_maps_empty_tool_ids(self) -> None:
        agent = _make_agent()
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = agent
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert result.tool_ids == ()

    @pytest.mark.asyncio
    async def test_maps_runtime_type(self) -> None:
        agent = _make_agent()
        agent.config = AgentConfig(runtime_type="basic")
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = agent
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert result.runtime_type == "basic"

    @pytest.mark.asyncio
    async def test_maps_enable_memory_true(self) -> None:
        agent = _make_agent()
        agent.config = AgentConfig(enable_memory=True)
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = agent
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert result.enable_memory is True

    @pytest.mark.asyncio
    async def test_maps_enable_memory_default_false(self) -> None:
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent()
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert result.enable_memory is False

    @pytest.mark.asyncio
    async def test_agent_id_none_raises_value_error(self) -> None:
        """Agent ID 为 None 时 _to_active_agent_info 抛出 ValueError。"""
        agent = _make_agent()
        agent.id = None  # type: ignore[assignment]
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = agent
        querier = AgentQuerierImpl(agent_repository=repo)

        with pytest.raises(ValueError, match="Agent ID 不能为空"):
            await querier.get_executable_agent(1)

    # ── TESTING 状态 + Blueprint 扩展字段 ──

    @pytest.mark.asyncio
    async def test_testing_agent_is_queryable(self) -> None:
        """TESTING 状态的 Agent 应可查询（用于测试沙盒）。"""
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = _make_agent(status=AgentStatus.TESTING)
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_no_session_factory_returns_empty_blueprint_fields(self) -> None:
        """无 session_factory 时 Blueprint 字段为空字符串（V1 兼容）。"""
        agent = _make_agent()
        agent.blueprint_id = 10
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = agent
        querier = AgentQuerierImpl(agent_repository=repo, session_factory=None)

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert result.workspace_path == ""
        assert result.runtime_arn == ""
        assert result.workspace_s3_uri == ""

    @pytest.mark.asyncio
    async def test_no_blueprint_id_returns_empty_blueprint_fields(self) -> None:
        """blueprint_id 为 None 时 Blueprint 字段为空字符串。"""
        agent = _make_agent()
        assert agent.blueprint_id is None
        repo = AsyncMock(spec=IAgentRepository)
        repo.get_by_id.return_value = agent
        querier = AgentQuerierImpl(agent_repository=repo)

        result = await querier.get_executable_agent(1)

        assert result is not None
        assert result.workspace_path == ""
        assert result.runtime_arn == ""
        assert result.workspace_s3_uri == ""

    def test_to_active_agent_info_with_blueprint_data(self) -> None:
        """_to_active_agent_info 正确填充 Blueprint 字段。"""
        agent = _make_agent()
        bp_data = {
            "workspace_path": "/workspaces/1",
            "runtime_arn": "arn:aws:agentcore:us-east-1:123:runtime/agent_1",
            "workspace_s3_uri": "s3://bucket/agent-workspaces/1/workspace.tar.gz",
        }

        result = AgentQuerierImpl._to_active_agent_info(agent, bp_data)

        assert result.workspace_path == "/workspaces/1"
        assert result.runtime_arn == "arn:aws:agentcore:us-east-1:123:runtime/agent_1"
        assert result.workspace_s3_uri == "s3://bucket/agent-workspaces/1/workspace.tar.gz"

    def test_to_active_agent_info_without_blueprint_data(self) -> None:
        """无 Blueprint 数据时三个字段为空字符串。"""
        agent = _make_agent()

        result = AgentQuerierImpl._to_active_agent_info(agent, None)

        assert result.workspace_path == ""
        assert result.runtime_arn == ""
        assert result.workspace_s3_uri == ""
