"""AgentRepositoryImpl 单元测试。"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.modules.agents.infrastructure.persistence.models.agent_model import AgentModel
from src.modules.agents.infrastructure.persistence.repositories.agent_repository_impl import (
    AgentRepositoryImpl,
)
from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45
from src.shared.infrastructure.pydantic_repository import PydanticRepository


@pytest.mark.unit
class TestAgentRepositoryImplStructure:
    def test_implements_iagent_repository(self) -> None:
        assert issubclass(AgentRepositoryImpl, IAgentRepository)

    def test_extends_pydantic_repository(self) -> None:
        assert issubclass(AgentRepositoryImpl, PydanticRepository)

    def test_entity_class_is_agent(self) -> None:
        assert AgentRepositoryImpl.entity_class is Agent

    def test_model_class_is_agent_model(self) -> None:
        assert AgentRepositoryImpl.model_class is AgentModel

    def test_updatable_fields_defined(self) -> None:
        expected = frozenset(
            {
                "name",
                "description",
                "system_prompt",
                "status",
                "model_id",
                "temperature",
                "max_tokens",
                "top_p",
                "stop_sequences",
                "runtime_type",
                "enable_teams",
            },
        )
        assert AgentRepositoryImpl._updatable_fields == expected


@pytest.mark.unit
class TestAgentRepositoryImplToEntity:
    def test_to_entity_converts_model_with_default_config(self) -> None:
        now = datetime.now(UTC)
        model = AgentModel(
            id=1,
            name="测试 Agent",
            description="描述",
            system_prompt="你是助手",
            status="draft",
            owner_id=42,
            model_id=MODEL_CLAUDE_HAIKU_45,
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
            stop_sequences="",
            runtime_type="agent",
            created_at=now,
            updated_at=now,
        )
        repo = AgentRepositoryImpl.__new__(AgentRepositoryImpl)
        entity = repo._to_entity(model)

        assert isinstance(entity, Agent)
        assert entity.id == 1
        assert entity.name == "测试 Agent"
        assert entity.description == "描述"
        assert entity.system_prompt == "你是助手"
        assert entity.status == AgentStatus.DRAFT
        assert entity.owner_id == 42
        assert entity.config.model_id == MODEL_CLAUDE_HAIKU_45
        assert entity.config.temperature == 0.7
        assert entity.config.max_tokens == 2048
        assert entity.config.top_p == 1.0
        assert entity.config.stop_sequences == ()
        assert entity.config.runtime_type == "agent"

    def test_to_entity_parses_stop_sequences_json(self) -> None:
        now = datetime.now(UTC)
        model = AgentModel(
            id=2,
            name="Agent",
            description="",
            system_prompt="",
            status="active",
            owner_id=1,
            model_id="model-1",
            temperature=0.5,
            max_tokens=1024,
            top_p=0.9,
            stop_sequences=json.dumps(["stop1", "stop2"]),
            runtime_type="agent",
            created_at=now,
            updated_at=now,
        )
        repo = AgentRepositoryImpl.__new__(AgentRepositoryImpl)
        entity = repo._to_entity(model)

        assert entity.config.stop_sequences == ("stop1", "stop2")
        assert entity.status == AgentStatus.ACTIVE


@pytest.mark.unit
class TestAgentRepositoryImplToModel:
    def test_to_model_converts_entity_with_default_config(self) -> None:
        agent = Agent(
            id=1,
            name="测试 Agent",
            description="描述",
            system_prompt="你是助手",
            status=AgentStatus.DRAFT,
            owner_id=42,
            config=AgentConfig(),
        )
        repo = AgentRepositoryImpl.__new__(AgentRepositoryImpl)
        model = repo._to_model(agent)

        assert isinstance(model, AgentModel)
        assert model.name == "测试 Agent"
        assert model.status == "draft"
        assert model.owner_id == 42
        assert model.model_id == MODEL_CLAUDE_HAIKU_45
        assert model.stop_sequences == ""
        assert model.runtime_type == "agent"

    def test_to_model_serializes_stop_sequences_to_json(self) -> None:
        agent = Agent(
            id=2,
            name="Agent",
            description="",
            system_prompt="",
            status=AgentStatus.ACTIVE,
            owner_id=1,
            config=AgentConfig(stop_sequences=("stop1", "stop2")),
        )
        repo = AgentRepositoryImpl.__new__(AgentRepositoryImpl)
        model = repo._to_model(agent)

        assert model.stop_sequences == json.dumps(["stop1", "stop2"])
        assert model.status == "active"


@pytest.mark.unit
class TestAgentRepositoryImplGetUpdateData:
    def test_get_update_data_flattens_config(self) -> None:
        agent = Agent(
            id=1,
            name="New Name",
            description="New Desc",
            system_prompt="New Prompt",
            status=AgentStatus.ACTIVE,
            owner_id=42,
            config=AgentConfig(temperature=0.5, max_tokens=1024),
        )
        repo = AgentRepositoryImpl.__new__(AgentRepositoryImpl)
        data = repo._get_update_data(agent)

        assert data["name"] == "New Name"
        assert data["description"] == "New Desc"
        assert data["system_prompt"] == "New Prompt"
        assert data["status"] == "active"
        assert data["model_id"] == MODEL_CLAUDE_HAIKU_45
        assert data["temperature"] == 0.5
        assert data["max_tokens"] == 1024
        assert data["top_p"] == 1.0
        assert data["stop_sequences"] == ""
        assert data["runtime_type"] == "agent"

    def test_get_update_data_only_includes_updatable_fields(self) -> None:
        agent = Agent(
            id=1,
            name="Name",
            description="",
            system_prompt="",
            status=AgentStatus.DRAFT,
            owner_id=42,
        )
        repo = AgentRepositoryImpl.__new__(AgentRepositoryImpl)
        data = repo._get_update_data(agent)

        # owner_id 不在 _updatable_fields 中
        assert "owner_id" not in data
        assert "id" not in data
        assert "created_at" not in data
        assert "updated_at" not in data


@pytest.mark.unit
class TestAgentRepositoryImplQueryMethods:
    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session: AsyncMock) -> AgentRepositoryImpl:
        return AgentRepositoryImpl(session=mock_session)

    @pytest.mark.asyncio
    async def test_get_by_name_and_owner_returns_none_when_not_found(
        self,
        repo: AgentRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_name_and_owner("不存在", owner_id=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name_and_owner_returns_agent_when_found(
        self,
        repo: AgentRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        now = datetime.now(UTC)
        mock_model = AgentModel(
            id=1,
            name="测试 Agent",
            description="",
            system_prompt="",
            status="draft",
            owner_id=42,
            model_id=MODEL_CLAUDE_HAIKU_45,
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
            stop_sequences="",
            runtime_type="agent",
            created_at=now,
            updated_at=now,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_name_and_owner("测试 Agent", owner_id=42)
        assert result is not None
        assert result.name == "测试 Agent"
        assert result.owner_id == 42

    @pytest.mark.asyncio
    async def test_count_by_owner_returns_count(
        self,
        repo: AgentRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result

        result = await repo.count_by_owner(owner_id=42)
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_by_owner_and_status_returns_count(
        self,
        repo: AgentRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        mock_session.execute.return_value = mock_result

        result = await repo.count_by_owner_and_status(
            owner_id=42,
            status=AgentStatus.ACTIVE,
        )
        assert result == 3

    @pytest.mark.asyncio
    async def test_list_by_owner_returns_empty_list(
        self,
        repo: AgentRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repo.list_by_owner(owner_id=42)
        assert result == []

    @pytest.mark.asyncio
    async def test_list_by_owner_and_status_returns_empty_list(
        self,
        repo: AgentRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repo.list_by_owner_and_status(
            owner_id=42,
            status=AgentStatus.DRAFT,
        )
        assert result == []
