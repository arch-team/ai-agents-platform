"""Agent 实体单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.domain.exceptions import ValidationError as DomainValidationError


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

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            Agent(name="", owner_id=1)

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            Agent(name="A" * 101, owner_id=1)

    def test_description_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="description"):
            Agent(name="Test", owner_id=1, description="A" * 501)

    def test_system_prompt_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="system_prompt"):
            Agent(name="Test", owner_id=1, system_prompt="A" * 10001)


@pytest.mark.unit
class TestAgentActivate:
    @pytest.fixture
    def draft_agent(self) -> Agent:
        return Agent(name="Test Agent", owner_id=1, system_prompt="你是助手")

    def test_activate_from_draft_succeeds(self, draft_agent: Agent) -> None:
        draft_agent.activate()
        assert draft_agent.status == AgentStatus.ACTIVE

    def test_activate_updates_timestamp(self, draft_agent: Agent) -> None:
        original = draft_agent.updated_at
        draft_agent.activate()
        assert draft_agent.updated_at is not None
        assert original is not None
        assert draft_agent.updated_at >= original

    def test_activate_without_system_prompt_raises(self) -> None:
        agent = Agent(name="Test", owner_id=1)
        with pytest.raises(DomainValidationError, match="系统提示词"):
            agent.activate()

    def test_activate_with_blank_system_prompt_raises(self) -> None:
        agent = Agent(name="Test", owner_id=1, system_prompt="   ")
        with pytest.raises(DomainValidationError, match="系统提示词"):
            agent.activate()

    def test_activate_from_active_raises(self, draft_agent: Agent) -> None:
        draft_agent.activate()
        with pytest.raises(InvalidStateTransitionError):
            draft_agent.activate()

    def test_activate_from_archived_raises(self, draft_agent: Agent) -> None:
        draft_agent.archive()
        with pytest.raises(InvalidStateTransitionError):
            draft_agent.activate()


@pytest.mark.unit
class TestAgentArchive:
    @pytest.fixture
    def draft_agent(self) -> Agent:
        return Agent(name="Test Agent", owner_id=1, system_prompt="你是助手")

    def test_archive_from_draft_succeeds(self, draft_agent: Agent) -> None:
        draft_agent.archive()
        assert draft_agent.status == AgentStatus.ARCHIVED

    def test_archive_from_active_succeeds(self, draft_agent: Agent) -> None:
        draft_agent.activate()
        draft_agent.archive()
        assert draft_agent.status == AgentStatus.ARCHIVED

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
