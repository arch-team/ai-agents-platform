"""Agent 实体单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.exceptions import InvalidStateTransitionError


@pytest.mark.unit
class TestAgentCreation:
    def test_create_agent_with_defaults(self) -> None:
        agent = Agent(name="Test Agent", owner_id=1)
        assert agent.name == "Test Agent"
        assert agent.description == ""
        assert agent.system_prompt == ""
        assert agent.status == AgentStatus.DRAFT
        assert agent.owner_id == 1
        assert agent.config == AgentConfig()

    def test_create_agent_with_custom_fields(self) -> None:
        config = AgentConfig(temperature=0.5, max_tokens=4096)
        agent = Agent(
            name="Custom Agent",
            description="一个自定义 Agent",
            system_prompt="你是一个助手",
            owner_id=2,
            config=config,
        )
        assert agent.name == "Custom Agent"
        assert agent.description == "一个自定义 Agent"
        assert agent.system_prompt == "你是一个助手"
        assert agent.config.temperature == 0.5

    def test_create_agent_inherits_pydantic_entity(self) -> None:
        agent = Agent(name="Test", owner_id=1)
        assert agent.id is None
        assert agent.created_at is not None
        assert agent.updated_at is not None

    @pytest.mark.parametrize(
        "field,kwargs",
        [
            ("name", {"name": "", "owner_id": 1}),
            ("name", {"name": "A" * 101, "owner_id": 1}),
            ("description", {"name": "Test", "owner_id": 1, "description": "A" * 501}),
            ("system_prompt", {"name": "Test", "owner_id": 1, "system_prompt": "A" * 10001}),
        ],
        ids=["empty_name", "name_too_long", "description_too_long", "system_prompt_too_long"],
    )
    def test_field_validation_raises(self, field: str, kwargs: dict) -> None:
        with pytest.raises(ValidationError, match=field):
            Agent(**kwargs)


@pytest.fixture
def draft_agent() -> Agent:
    """草稿 Agent。"""
    return Agent(name="Test Agent", owner_id=1, system_prompt="你是助手")


@pytest.fixture
def testing_agent() -> Agent:
    """TESTING 状态的 Agent（可激活）。"""
    agent = Agent(name="Test Agent", owner_id=1, system_prompt="你是助手")
    agent.start_testing()
    return agent


@pytest.mark.unit
class TestAgentActivate:
    """activate() 仅允许 TESTING -> ACTIVE (V1 DRAFT->ACTIVE 路径已移除)。"""

    def test_activate_from_testing_succeeds(self, testing_agent: Agent) -> None:
        testing_agent.activate()
        assert testing_agent.status == AgentStatus.ACTIVE

    def test_activate_updates_timestamp(self, testing_agent: Agent) -> None:
        original = testing_agent.updated_at
        testing_agent.activate()
        assert testing_agent.updated_at is not None
        assert original is not None
        assert testing_agent.updated_at >= original

    def test_activate_from_draft_raises(self) -> None:
        """DRAFT 不能直接激活，必须先经过 TESTING。"""
        agent = Agent(name="Test", owner_id=1, system_prompt="提示")
        with pytest.raises(InvalidStateTransitionError):
            agent.activate()

    def test_activate_from_active_raises(self, testing_agent: Agent) -> None:
        testing_agent.activate()
        with pytest.raises(InvalidStateTransitionError):
            testing_agent.activate()

    def test_activate_from_archived_raises(self, draft_agent: Agent) -> None:
        draft_agent.archive()
        with pytest.raises(InvalidStateTransitionError):
            draft_agent.activate()


@pytest.mark.unit
class TestAgentStartTesting:
    """start_testing(): DRAFT -> TESTING。"""

    def test_start_testing_from_draft(self, draft_agent: Agent) -> None:
        draft_agent.start_testing()
        assert draft_agent.status == AgentStatus.TESTING

    def test_start_testing_from_active_raises(self, testing_agent: Agent) -> None:
        testing_agent.activate()
        with pytest.raises(InvalidStateTransitionError):
            testing_agent.start_testing()


@pytest.mark.unit
class TestAgentArchive:
    def test_archive_from_draft_succeeds(self, draft_agent: Agent) -> None:
        draft_agent.archive()
        assert draft_agent.status == AgentStatus.ARCHIVED

    def test_archive_from_testing_succeeds(self, testing_agent: Agent) -> None:
        testing_agent.archive()
        assert testing_agent.status == AgentStatus.ARCHIVED

    def test_archive_from_active_succeeds(self, testing_agent: Agent) -> None:
        testing_agent.activate()
        testing_agent.archive()
        assert testing_agent.status == AgentStatus.ARCHIVED

    def test_archive_updates_timestamp(self, draft_agent: Agent) -> None:
        original = draft_agent.updated_at
        draft_agent.archive()
        assert draft_agent.updated_at is not None
        assert original is not None
        assert draft_agent.updated_at >= original

    def test_archive_from_archived_raises(self, draft_agent: Agent) -> None:
        draft_agent.archive()
        with pytest.raises(InvalidStateTransitionError):
            draft_agent.archive()
