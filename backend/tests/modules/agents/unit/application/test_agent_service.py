"""AgentService 测试。"""

from unittest.mock import AsyncMock

import pytest

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
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.exceptions import (
    DomainError,
    InvalidStateTransitionError,
)
from tests.modules.agents.conftest import make_agent


@pytest.mark.unit
class TestAgentServiceCreate:
    @pytest.mark.asyncio
    async def test_create_agent_success(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_agent_repo.get_by_name_and_owner.return_value = None
        mock_agent_repo.create.side_effect = lambda a: make_agent(
            name=a.name,
            description=a.description,
            owner_id=a.owner_id,
        )

        dto = CreateAgentDTO(name="新 Agent", description="新描述")
        result = await agent_service.create_agent(dto, owner_id=100)

        assert result.name == "新 Agent"
        assert result.description == "新描述"
        assert result.status == "draft"
        assert result.owner_id == 100
        mock_agent_repo.create.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_duplicate_name_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_name_and_owner.return_value = make_agent(name="已存在")

        dto = CreateAgentDTO(name="已存在")

        with pytest.raises(AgentNameDuplicateError):
            await agent_service.create_agent(dto, owner_id=100)

        mock_agent_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_agent_uses_dto_config(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_agent_repo.get_by_name_and_owner.return_value = None
        created_agent: Agent | None = None

        async def capture_create(agent: Agent) -> Agent:
            nonlocal created_agent
            created_agent = agent
            return make_agent(
                name=agent.name,
                owner_id=agent.owner_id,
                config=agent.config,
            )

        mock_agent_repo.create.side_effect = capture_create

        dto = CreateAgentDTO(
            name="自定义配置",
            model_id="custom-model",
            temperature=0.5,
            max_tokens=4096,
        )
        await agent_service.create_agent(dto, owner_id=100)

        assert created_agent is not None
        assert created_agent.config.model_id == "custom-model"
        assert created_agent.config.temperature == 0.5
        assert created_agent.config.max_tokens == 4096

    @pytest.mark.asyncio
    async def test_create_agent_with_tool_ids(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_agent_repo.get_by_name_and_owner.return_value = None
        created_agent: Agent | None = None

        async def capture_create(agent: Agent) -> Agent:
            nonlocal created_agent
            created_agent = agent
            return make_agent(
                name=agent.name,
                owner_id=agent.owner_id,
                config=agent.config,
            )

        mock_agent_repo.create.side_effect = capture_create

        dto = CreateAgentDTO(name="带工具 Agent", tool_ids=[10, 20, 30])
        result = await agent_service.create_agent(dto, owner_id=100)

        assert created_agent is not None
        assert created_agent.config.tool_ids == (10, 20, 30)
        assert result.tool_ids == [10, 20, 30]


@pytest.mark.unit
class TestAgentServiceGet:
    @pytest.mark.asyncio
    async def test_get_agent_returns_dto(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = make_agent()

        result = await agent_service.get_agent(1)

        assert result.id == 1
        assert result.name == "测试 Agent"

    @pytest.mark.asyncio
    async def test_get_agent_not_found_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = None

        with pytest.raises(AgentNotFoundError):
            await agent_service.get_agent(9999)


@pytest.mark.unit
class TestAgentServiceList:
    @pytest.mark.asyncio
    async def test_list_agents_returns_paged_result(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.list_by_owner.return_value = [
            make_agent(agent_id=1, name="A1"),
            make_agent(agent_id=2, name="A2"),
        ]
        mock_agent_repo.count_by_owner.return_value = 2

        result = await agent_service.list_agents(owner_id=100)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_agents_empty(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.list_by_owner.return_value = []
        mock_agent_repo.count_by_owner.return_value = 0

        result = await agent_service.list_agents(owner_id=100)

        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_agents_by_status(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.list_by_owner_and_status.return_value = [
            make_agent(agent_id=1, status=AgentStatus.ACTIVE),
        ]
        mock_agent_repo.count_by_owner_and_status.return_value = 1

        result = await agent_service.list_agents(owner_id=100, status=AgentStatus.ACTIVE)

        assert result.total == 1
        assert len(result.items) == 1
        mock_agent_repo.list_by_owner_and_status.assert_called_once_with(
            100,
            AgentStatus.ACTIVE,
            offset=0,
            limit=20,
        )

    @pytest.mark.asyncio
    async def test_list_agents_pagination(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.list_by_owner.return_value = [
            make_agent(agent_id=3, name="A3"),
        ]
        mock_agent_repo.count_by_owner.return_value = 5

        result = await agent_service.list_agents(owner_id=100, page=2, page_size=2)

        assert result.page == 2
        assert result.page_size == 2
        assert result.total == 5
        mock_agent_repo.list_by_owner.assert_called_once_with(100, offset=2, limit=2)


@pytest.mark.unit
class TestAgentServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_draft_agent_success(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        agent = make_agent(status=AgentStatus.DRAFT)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.get_by_name_and_owner.return_value = None
        mock_agent_repo.update.side_effect = lambda a: a

        dto = UpdateAgentDTO(name="新名称", description="新描述")
        result = await agent_service.update_agent(1, dto, operator_id=100)

        assert result.name == "新名称"
        assert result.description == "新描述"
        mock_agent_repo.update.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = None

        dto = UpdateAgentDTO(name="新名称")

        with pytest.raises(AgentNotFoundError):
            await agent_service.update_agent(9999, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_non_owner_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = make_agent(owner_id=100)

        dto = UpdateAgentDTO(name="新名称")

        with pytest.raises(DomainError, match="无权操作"):
            await agent_service.update_agent(1, dto, operator_id=999)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", [AgentStatus.ACTIVE, AgentStatus.ARCHIVED])
    async def test_update_non_draft_agent_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        status: AgentStatus,
    ) -> None:
        agent = make_agent(status=status, system_prompt="prompt")
        mock_agent_repo.get_by_id.return_value = agent

        dto = UpdateAgentDTO(name="新名称")

        with pytest.raises(InvalidStateTransitionError):
            await agent_service.update_agent(1, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_partial_fields(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        agent = make_agent(status=AgentStatus.DRAFT)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.side_effect = lambda a: a

        dto = UpdateAgentDTO(temperature=0.9)
        result = await agent_service.update_agent(1, dto, operator_id=100)

        assert result.temperature == 0.9
        assert result.name == "测试 Agent"

    @pytest.mark.asyncio
    async def test_update_duplicate_name_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        agent = make_agent(status=AgentStatus.DRAFT, name="原始名称")
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.get_by_name_and_owner.return_value = make_agent(
            agent_id=2,
            name="已存在",
        )

        dto = UpdateAgentDTO(name="已存在")

        with pytest.raises(AgentNameDuplicateError):
            await agent_service.update_agent(1, dto, operator_id=100)

    @pytest.mark.asyncio
    async def test_update_tool_ids(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        agent = make_agent(status=AgentStatus.DRAFT)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.side_effect = lambda a: a

        dto = UpdateAgentDTO(tool_ids=[5, 10, 15])
        result = await agent_service.update_agent(1, dto, operator_id=100)

        assert result.tool_ids == [5, 10, 15]
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tool_ids_none_keeps_original(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        agent = make_agent(
            status=AgentStatus.DRAFT,
            config=AgentConfig(tool_ids=(1, 2)),
        )
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.side_effect = lambda a: a

        dto = UpdateAgentDTO(temperature=0.5)
        result = await agent_service.update_agent(1, dto, operator_id=100)

        assert result.tool_ids == [1, 2]


@pytest.mark.unit
class TestAgentServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_draft_agent_success(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = make_agent(status=AgentStatus.DRAFT)

        await agent_service.delete_agent(1, operator_id=100)

        mock_agent_repo.delete.assert_called_once_with(1)
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = None

        with pytest.raises(AgentNotFoundError):
            await agent_service.delete_agent(9999, operator_id=100)

    @pytest.mark.asyncio
    async def test_delete_active_agent_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = make_agent(
            status=AgentStatus.ACTIVE,
            system_prompt="prompt",
        )

        with pytest.raises(InvalidStateTransitionError):
            await agent_service.delete_agent(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_delete_non_owner_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = make_agent(owner_id=100)

        with pytest.raises(DomainError, match="无权操作"):
            await agent_service.delete_agent(1, operator_id=999)


@pytest.mark.unit
class TestAgentServiceActivate:
    @pytest.mark.asyncio
    async def test_activate_testing_agent_success(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        agent = make_agent(status=AgentStatus.TESTING, system_prompt="你是一个助手")
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.side_effect = lambda a: a

        result = await agent_service.activate_agent(1, operator_id=100)

        assert result.status == "active"
        mock_agent_repo.update.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_from_draft_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        """DRAFT 不能直接激活，必须先经过 TESTING。"""
        mock_agent_repo.get_by_id.return_value = make_agent(
            status=AgentStatus.DRAFT,
            system_prompt="prompt",
        )

        with pytest.raises(InvalidStateTransitionError):
            await agent_service.activate_agent(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_activate_from_active_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = make_agent(
            status=AgentStatus.ACTIVE,
            system_prompt="prompt",
        )

        with pytest.raises(InvalidStateTransitionError):
            await agent_service.activate_agent(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_activate_not_found_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = None

        with pytest.raises(AgentNotFoundError):
            await agent_service.activate_agent(9999, operator_id=100)


@pytest.mark.unit
class TestAgentServiceArchive:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "status,system_prompt",
        [
            (AgentStatus.ACTIVE, "prompt"),
            (AgentStatus.DRAFT, ""),
        ],
        ids=["from_active", "from_draft"],
    )
    async def test_archive_success(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
        status: AgentStatus,
        system_prompt: str,
    ) -> None:
        agent = make_agent(status=status, system_prompt=system_prompt)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.side_effect = lambda a: a

        result = await agent_service.archive_agent(1, operator_id=100)

        assert result.status == "archived"

    @pytest.mark.asyncio
    async def test_archive_already_archived_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = make_agent(status=AgentStatus.ARCHIVED)

        with pytest.raises(InvalidStateTransitionError):
            await agent_service.archive_agent(1, operator_id=100)

    @pytest.mark.asyncio
    async def test_archive_not_found_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = None

        with pytest.raises(AgentNotFoundError):
            await agent_service.archive_agent(9999, operator_id=100)

    @pytest.mark.asyncio
    async def test_archive_non_owner_raises(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
    ) -> None:
        mock_agent_repo.get_by_id.return_value = make_agent(owner_id=100)

        with pytest.raises(DomainError, match="无权操作"):
            await agent_service.archive_agent(1, operator_id=999)


@pytest.mark.unit
class TestAgentServiceEnableMemory:
    """enable_memory 字段的 CRUD 测试。"""

    @pytest.mark.asyncio
    async def test_create_agent_with_enable_memory_true(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_agent_repo.get_by_name_and_owner.return_value = None
        mock_agent_repo.create.side_effect = lambda a: make_agent(
            name=a.name,
            config=a.config,
        )

        dto = CreateAgentDTO(name="Memory Agent", enable_memory=True)
        result = await agent_service.create_agent(dto, owner_id=100)

        assert result.enable_memory is True

    @pytest.mark.asyncio
    async def test_create_agent_enable_memory_default_false(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_agent_repo.get_by_name_and_owner.return_value = None
        mock_agent_repo.create.side_effect = lambda a: make_agent(
            name=a.name,
            config=a.config,
        )

        dto = CreateAgentDTO(name="No Memory Agent")
        result = await agent_service.create_agent(dto, owner_id=100)

        assert result.enable_memory is False

    @pytest.mark.asyncio
    async def test_update_enable_memory(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        agent = make_agent(status=AgentStatus.DRAFT)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.side_effect = lambda a: a

        dto = UpdateAgentDTO(enable_memory=True)
        result = await agent_service.update_agent(1, dto, operator_id=100)

        assert result.enable_memory is True

    @pytest.mark.asyncio
    async def test_update_enable_memory_none_keeps_original(
        self,
        mock_agent_repo: AsyncMock,
        agent_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        agent = make_agent(
            status=AgentStatus.DRAFT,
            config=AgentConfig(enable_memory=True),
        )
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.side_effect = lambda a: a

        dto = UpdateAgentDTO(temperature=0.5)
        result = await agent_service.update_agent(1, dto, operator_id=100)

        assert result.enable_memory is True
