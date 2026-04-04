"""AgentCreatorImpl 单元测试 — V1/V2 创建 + start_testing。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.agents.application.dto.agent_dto import AgentDTO
from src.modules.agents.application.interfaces.workspace_manager import IWorkspaceManager
from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.domain.repositories.agent_blueprint_repository import IAgentBlueprintRepository
from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.modules.agents.infrastructure.services.agent_creator_impl import AgentCreatorImpl
from src.shared.domain.interfaces.agent_creator import (
    BlueprintData,
    CreateAgentRequest,
    CreateAgentWithBlueprintRequest,
    GuardrailData,
    PersonaData,
    ToolBindingData,
)
from tests.modules.agents.conftest import make_agent


def _make_agent_dto(**overrides: object) -> AgentDTO:
    from datetime import UTC, datetime

    now = datetime.now(tz=UTC)
    defaults: dict[str, object] = {
        "id": 1,
        "name": "测试 Agent",
        "description": "描述",
        "system_prompt": "prompt",
        "status": "draft",
        "owner_id": 100,
        "model_id": "claude-sonnet-4-20250514",
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
        "runtime_type": "cloud",
        "enable_teams": False,
        "enable_memory": False,
        "created_at": now,
        "updated_at": now,
        "tool_ids": [],
    }
    defaults.update(overrides)
    return AgentDTO(**defaults)  # type: ignore[arg-type]


@pytest.fixture
def mock_agent_service() -> AsyncMock:
    return AsyncMock(spec=AgentService)


@pytest.fixture
def mock_agent_repo() -> AsyncMock:
    return AsyncMock(spec=IAgentRepository)


@pytest.fixture
def mock_blueprint_repo() -> AsyncMock:
    return AsyncMock(spec=IAgentBlueprintRepository)


@pytest.fixture
def mock_workspace_mgr() -> AsyncMock:
    return AsyncMock(spec=IWorkspaceManager)


@pytest.mark.unit
class TestCreateAgentV1:
    """V1: 简单 Agent 创建。"""

    @pytest.mark.asyncio
    async def test_create_agent_delegates_to_service(self, mock_agent_service: AsyncMock) -> None:
        dto = _make_agent_dto(id=42, name="V1 Agent")
        mock_agent_service.create_agent.return_value = dto
        creator = AgentCreatorImpl(agent_service=mock_agent_service)

        result = await creator.create_agent(
            CreateAgentRequest(name="V1 Agent", system_prompt="prompt", description="desc"),
            owner_id=100,
        )

        assert result.id == 42
        assert result.name == "V1 Agent"
        mock_agent_service.create_agent.assert_awaited_once()


@pytest.mark.unit
class TestCreateAgentWithBlueprintV2:
    """V2: Agent + Blueprint + Workspace 创建。"""

    @pytest.mark.asyncio
    async def test_full_flow(
        self,
        mock_agent_service: AsyncMock,
        mock_agent_repo: AsyncMock,
        mock_blueprint_repo: AsyncMock,
        mock_workspace_mgr: AsyncMock,
    ) -> None:
        from pathlib import Path

        agent_dto = _make_agent_dto(id=10, name="V2 Agent")
        mock_agent_service.create_agent.return_value = agent_dto
        mock_blueprint_repo.create_blueprint.return_value = 99
        mock_agent_repo.get_by_id.return_value = make_agent(agent_id=10)
        mock_workspace_mgr.create_workspace.return_value = Path("/tmp/ws/10")

        creator = AgentCreatorImpl(
            agent_service=mock_agent_service,
            agent_repository=mock_agent_repo,
            blueprint_repository=mock_blueprint_repo,
            workspace_manager=mock_workspace_mgr,
        )

        request = CreateAgentWithBlueprintRequest(
            name="V2 Agent",
            description="desc",
            blueprint=BlueprintData(
                persona=PersonaData(role="客服", background="安克售后"),
                guardrails=[GuardrailData(rule="不能承诺退款", severity="block")],
                tool_bindings=[ToolBindingData(tool_id=1, display_name="订单查询", usage_hint="查订单")],
                skill_ids=[3],
                skill_paths=["published/return-processing/v1"],
            ),
        )

        from src.shared.domain.interfaces.agent_creator import CreatedAgentInfo

        with patch.object(
            AgentCreatorImpl,
            "create_agent",
            return_value=CreatedAgentInfo(id=10, name="V2 Agent", status="draft"),
        ):
            creator_fresh = AgentCreatorImpl(
                agent_service=mock_agent_service,
                agent_repository=mock_agent_repo,
                blueprint_repository=mock_blueprint_repo,
                workspace_manager=mock_workspace_mgr,
            )
            result = await creator_fresh.create_agent_with_blueprint(request, owner_id=100)

        assert result.id == 10
        mock_blueprint_repo.create_blueprint.assert_awaited_once()
        mock_workspace_mgr.create_workspace.assert_awaited_once()
        mock_blueprint_repo.update_workspace_path.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fallback_without_deps(self, mock_agent_service: AsyncMock) -> None:
        """没有 blueprint_repo/workspace_manager 时降级到 V1。"""
        creator = AgentCreatorImpl(agent_service=mock_agent_service)

        agent_dto = _make_agent_dto(id=1, name="降级 Agent")
        mock_agent_service.create_agent.return_value = agent_dto

        request = CreateAgentWithBlueprintRequest(
            name="降级 Agent",
            description="desc",
            blueprint=BlueprintData(persona=PersonaData(role="助手", background="通用")),
        )
        result = await creator.create_agent_with_blueprint(request, owner_id=100)

        assert result.id == 1
        assert result.name == "降级 Agent"


@pytest.mark.unit
class TestStartTesting:
    """start_testing 代理到 AgentService。"""

    @pytest.mark.asyncio
    async def test_start_testing_delegates(self, mock_agent_service: AsyncMock) -> None:
        dto = _make_agent_dto(id=5, name="Testing Agent", status="testing")
        mock_agent_service.start_testing.return_value = dto
        creator = AgentCreatorImpl(agent_service=mock_agent_service)

        result = await creator.start_testing(agent_id=5, operator_id=100)

        assert result.id == 5
        assert result.status == "testing"
        mock_agent_service.start_testing.assert_awaited_once_with(5, 100)
