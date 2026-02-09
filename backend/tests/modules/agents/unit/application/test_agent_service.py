"""AgentService 测试。"""

import pytest
from unittest.mock import AsyncMock, patch

from src.modules.agents.application.dto.agent_dto import (
    CreateAgentDTO,
    UpdateAgentDTO,
)
from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.exceptions import (
    AgentNameDuplicateError,
    AgentNotFoundError,
)
from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.exceptions import (
    DomainError,
    InvalidStateTransitionError,
    ValidationError,
)


def _make_agent(
    *,
    agent_id: int = 1,
    name: str = "测试 Agent",
    description: str = "描述",
    system_prompt: str = "",
    status: AgentStatus = AgentStatus.DRAFT,
    owner_id: int = 100,
    config: AgentConfig | None = None,
) -> Agent:
    return Agent(
        id=agent_id,
        name=name,
        description=description,
        system_prompt=system_prompt,
        status=status,
        owner_id=owner_id,
        config=config or AgentConfig(),
    )


def _make_service(mock_repo: AsyncMock) -> AgentService:
    return AgentService(mock_repo)


@pytest.mark.unit
class TestAgentServiceCreate:
    @pytest.mark.asyncio
    async def test_create_agent_success(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_name_and_owner.return_value = None
        mock_repo.create.side_effect = lambda a: _make_agent(
            name=a.name, description=a.description, owner_id=a.owner_id
        )

        service = _make_service(mock_repo)
        dto = CreateAgentDTO(name="新 Agent", description="新描述")

        with patch(
            "src.modules.agents.application.services.agent_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.create_agent(dto, owner_id=100)

        assert result.name == "新 Agent"
        assert result.description == "新描述"
        assert result.status == "draft"
        assert result.owner_id == 100
        mock_repo.create.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_duplicate_name_raises(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_name_and_owner.return_value = _make_agent(name="已存在")

        service = _make_service(mock_repo)
        dto = CreateAgentDTO(name="已存在")

        with pytest.raises(AgentNameDuplicateError):
            await service.create_agent(dto, owner_id=100)

        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_agent_uses_dto_config(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_name_and_owner.return_value = None
        created_agent: Agent | None = None

        async def capture_create(agent: Agent) -> Agent:
            nonlocal created_agent
            created_agent = agent
            return _make_agent(
                name=agent.name, owner_id=agent.owner_id, config=agent.config
            )

        mock_repo.create.side_effect = capture_create

        service = _make_service(mock_repo)
        dto = CreateAgentDTO(
            name="自定义配置",
            model_id="custom-model",
            temperature=0.5,
            max_tokens=4096,
        )

        with patch(
            "src.modules.agents.application.services.agent_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            await service.create_agent(dto, owner_id=100)

        assert created_agent is not None
        assert created_agent.config.model_id == "custom-model"
        assert created_agent.config.temperature == 0.5
        assert created_agent.config.max_tokens == 4096


@pytest.mark.unit
class TestAgentServiceGet:
    @pytest.mark.asyncio
    async def test_get_agent_returns_dto(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = _make_agent()

        service = _make_service(mock_repo)
        result = await service.get_agent(1)

        assert result.id == 1
        assert result.name == "测试 Agent"

    @pytest.mark.asyncio
    async def test_get_agent_not_found_raises(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = None

        service = _make_service(mock_repo)

        with pytest.raises(AgentNotFoundError):
            await service.get_agent(9999)


@pytest.mark.unit
class TestAgentServiceList:
    @pytest.mark.asyncio
    async def test_list_agents_returns_paged_result(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.list_by_owner.return_value = [
            _make_agent(agent_id=1, name="A1"),
            _make_agent(agent_id=2, name="A2"),
        ]
        mock_repo.count_by_owner.return_value = 2

        service = _make_service(mock_repo)
        result = await service.list_agents(owner_id=100)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_agents_empty(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.list_by_owner.return_value = []
        mock_repo.count_by_owner.return_value = 0

        service = _make_service(mock_repo)
        result = await service.list_agents(owner_id=100)

        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_agents_by_status(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.list_by_owner_and_status.return_value = [
            _make_agent(agent_id=1, status=AgentStatus.ACTIVE),
        ]
        mock_repo.count_by_owner_and_status.return_value = 1

        service = _make_service(mock_repo)
        result = await service.list_agents(owner_id=100, status=AgentStatus.ACTIVE)

        assert result.total == 1
        assert len(result.items) == 1
        mock_repo.list_by_owner_and_status.assert_called_once_with(
            100, AgentStatus.ACTIVE, offset=0, limit=20
        )

    @pytest.mark.asyncio
    async def test_list_agents_pagination(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.list_by_owner.return_value = [
            _make_agent(agent_id=3, name="A3"),
        ]
        mock_repo.count_by_owner.return_value = 5

        service = _make_service(mock_repo)
        result = await service.list_agents(owner_id=100, page=2, page_size=2)

        assert result.page == 2
        assert result.page_size == 2
        assert result.total == 5
        mock_repo.list_by_owner.assert_called_once_with(100, offset=2, limit=2)


@pytest.mark.unit
class TestAgentServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_draft_agent_success(self) -> None:
        agent = _make_agent(status=AgentStatus.DRAFT)
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent
        mock_repo.get_by_name_and_owner.return_value = None
        mock_repo.update.side_effect = lambda a: a

        service = _make_service(mock_repo)
        dto = UpdateAgentDTO(name="新名称", description="新描述")

        with patch(
            "src.modules.agents.application.services.agent_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.update_agent(1, dto, operator_id=100)

        assert result.name == "新名称"
        assert result.description == "新描述"
        mock_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found_raises(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = None

        service = _make_service(mock_repo)
        dto = UpdateAgentDTO(name="新名称")

        with pytest.raises(AgentNotFoundError):
            await service.update_agent(9999, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_non_owner_raises(self) -> None:
        agent = _make_agent(owner_id=100)
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)
        dto = UpdateAgentDTO(name="新名称")

        with pytest.raises(DomainError, match="无权操作"):
            await service.update_agent(1, dto, operator_id=999)

    @pytest.mark.asyncio
    async def test_update_active_agent_raises(self) -> None:
        agent = _make_agent(status=AgentStatus.ACTIVE, system_prompt="prompt")
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)
        dto = UpdateAgentDTO(name="新名称")

        with pytest.raises(InvalidStateTransitionError):
            await service.update_agent(1, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_archived_agent_raises(self) -> None:
        agent = _make_agent(status=AgentStatus.ARCHIVED)
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)
        dto = UpdateAgentDTO(description="新描述")

        with pytest.raises(InvalidStateTransitionError):
            await service.update_agent(1, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_partial_fields(self) -> None:
        agent = _make_agent(status=AgentStatus.DRAFT)
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent
        mock_repo.update.side_effect = lambda a: a

        service = _make_service(mock_repo)
        dto = UpdateAgentDTO(temperature=0.9)

        with patch(
            "src.modules.agents.application.services.agent_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.update_agent(1, dto, operator_id=100)

        assert result.temperature == 0.9
        # 其他字段不变
        assert result.name == "测试 Agent"

    @pytest.mark.asyncio
    async def test_update_duplicate_name_raises(self) -> None:
        agent = _make_agent(status=AgentStatus.DRAFT, name="原始名称")
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent
        mock_repo.get_by_name_and_owner.return_value = _make_agent(
            agent_id=2, name="已存在"
        )

        service = _make_service(mock_repo)
        dto = UpdateAgentDTO(name="已存在")

        with pytest.raises(AgentNameDuplicateError):
            await service.update_agent(1, dto, operator_id=100)


@pytest.mark.unit
class TestAgentServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_draft_agent_success(self) -> None:
        agent = _make_agent(status=AgentStatus.DRAFT)
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)

        with patch(
            "src.modules.agents.application.services.agent_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            await service.delete_agent(1, operator_id=100)

        mock_repo.delete.assert_called_once_with(1)
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_raises(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = None

        service = _make_service(mock_repo)

        with pytest.raises(AgentNotFoundError):
            await service.delete_agent(9999, operator_id=100)

    @pytest.mark.asyncio
    async def test_delete_active_agent_raises(self) -> None:
        agent = _make_agent(status=AgentStatus.ACTIVE, system_prompt="prompt")
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)

        with pytest.raises(InvalidStateTransitionError):
            await service.delete_agent(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_delete_non_owner_raises(self) -> None:
        agent = _make_agent(owner_id=100)
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)

        with pytest.raises(DomainError, match="无权操作"):
            await service.delete_agent(1, operator_id=999)


@pytest.mark.unit
class TestAgentServiceActivate:
    @pytest.mark.asyncio
    async def test_activate_draft_agent_success(self) -> None:
        agent = _make_agent(
            status=AgentStatus.DRAFT, system_prompt="你是一个助手"
        )
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent
        mock_repo.update.side_effect = lambda a: a

        service = _make_service(mock_repo)

        with patch(
            "src.modules.agents.application.services.agent_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.activate_agent(1, operator_id=100)

        assert result.status == "active"
        mock_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_non_draft_raises(self) -> None:
        agent = _make_agent(status=AgentStatus.ACTIVE, system_prompt="prompt")
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)

        with pytest.raises(InvalidStateTransitionError):
            await service.activate_agent(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_activate_without_system_prompt_raises(self) -> None:
        agent = _make_agent(status=AgentStatus.DRAFT, system_prompt="")
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)

        with pytest.raises(ValidationError, match="系统提示词"):
            await service.activate_agent(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_activate_not_found_raises(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = None

        service = _make_service(mock_repo)

        with pytest.raises(AgentNotFoundError):
            await service.activate_agent(9999, operator_id=100)


@pytest.mark.unit
class TestAgentServiceArchive:
    @pytest.mark.asyncio
    async def test_archive_active_agent_success(self) -> None:
        agent = _make_agent(status=AgentStatus.ACTIVE, system_prompt="prompt")
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent
        mock_repo.update.side_effect = lambda a: a

        service = _make_service(mock_repo)

        with patch(
            "src.modules.agents.application.services.agent_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.archive_agent(1, operator_id=100)

        assert result.status == "archived"
        mock_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive_draft_agent_success(self) -> None:
        agent = _make_agent(status=AgentStatus.DRAFT)
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent
        mock_repo.update.side_effect = lambda a: a

        service = _make_service(mock_repo)

        with patch(
            "src.modules.agents.application.services.agent_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.archive_agent(1, operator_id=100)

        assert result.status == "archived"

    @pytest.mark.asyncio
    async def test_archive_already_archived_raises(self) -> None:
        agent = _make_agent(status=AgentStatus.ARCHIVED)
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)

        with pytest.raises(InvalidStateTransitionError):
            await service.archive_agent(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_archive_not_found_raises(self) -> None:
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = None

        service = _make_service(mock_repo)

        with pytest.raises(AgentNotFoundError):
            await service.archive_agent(9999, operator_id=100)

    @pytest.mark.asyncio
    async def test_archive_non_owner_raises(self) -> None:
        agent = _make_agent(owner_id=100)
        mock_repo = AsyncMock(spec=IAgentRepository)
        mock_repo.get_by_id.return_value = agent

        service = _make_service(mock_repo)

        with pytest.raises(DomainError, match="无权操作"):
            await service.archive_agent(1, operator_id=999)
