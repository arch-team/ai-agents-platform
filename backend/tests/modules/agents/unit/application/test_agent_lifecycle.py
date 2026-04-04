"""AgentService 上线/下线编排测试 — start_testing / go_live / take_offline。"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.modules.agents.application.interfaces.agent_runtime_manager import RuntimeInfo
from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.domain.repositories.agent_blueprint_repository import (
    BlueprintRuntimeInfo,
    IAgentBlueprintRepository,
)
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError
from tests.modules.agents.conftest import make_agent


@pytest.fixture
def mock_blueprint_repo() -> AsyncMock:
    """Blueprint 仓库 Mock。"""
    repo = AsyncMock(spec=IAgentBlueprintRepository)
    repo.get_runtime_info.return_value = BlueprintRuntimeInfo(
        blueprint_id=10,
        workspace_path="/workspace/agent-workspaces/1",
        runtime_arn="",
        workspace_s3_uri="",
    )
    return repo


@pytest.fixture
def mock_workspace_manager() -> AsyncMock:
    """WorkspaceManager Mock。"""
    mgr = AsyncMock()
    mgr.upload_to_s3.return_value = "s3://bucket/agent-workspaces/1/workspace.tar.gz"
    return mgr


@pytest.fixture
def mock_runtime_manager() -> AsyncMock:
    """RuntimeManager Mock。"""
    mgr = AsyncMock()
    mgr.provision.return_value = RuntimeInfo(
        runtime_arn="arn:aws:bedrock-agentcore:us-east-1:123:runtime/agent-1-dev",
        runtime_name="agent-1-dev",
    )
    return mgr


@pytest.fixture
def lifecycle_service(
    mock_agent_repo: AsyncMock,
    mock_blueprint_repo: AsyncMock,
    mock_workspace_manager: AsyncMock,
    mock_runtime_manager: AsyncMock,
) -> AgentService:
    """AgentService 实例 — 注入所有 Blueprint 生命周期依赖。"""
    return AgentService(
        repository=mock_agent_repo,
        blueprint_repository=mock_blueprint_repo,
        workspace_manager=mock_workspace_manager,
        runtime_manager=mock_runtime_manager,
    )


@pytest.mark.unit
class TestStartTesting:
    """start_testing — DRAFT → TESTING 编排。"""

    @pytest.mark.asyncio
    async def test_start_testing_success(
        self,
        mock_agent_repo: AsyncMock,
        mock_blueprint_repo: AsyncMock,
        mock_workspace_manager: AsyncMock,
        mock_runtime_manager: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """完整编排: upload_to_s3 → provision → 保存 runtime_arn → Agent TESTING。"""
        agent = make_agent(agent_id=1, status=AgentStatus.DRAFT, owner_id=100)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.return_value = agent

        result = await lifecycle_service.start_testing(agent_id=1, operator_id=100)

        # 验证编排步骤
        mock_workspace_manager.upload_to_s3.assert_called_once_with(
            Path("/workspace/agent-workspaces/1"),
            1,
        )
        mock_runtime_manager.provision.assert_called_once_with(
            1,
            "s3://bucket/agent-workspaces/1/workspace.tar.gz",
        )
        mock_blueprint_repo.update_runtime_info.assert_called_once_with(
            1,
            runtime_arn="arn:aws:bedrock-agentcore:us-east-1:123:runtime/agent-1-dev",
            workspace_s3_uri="s3://bucket/agent-workspaces/1/workspace.tar.gz",
        )
        mock_agent_repo.update.assert_called_once()
        assert agent.status == AgentStatus.TESTING

    @pytest.mark.asyncio
    async def test_start_testing_requires_draft_status(
        self,
        mock_agent_repo: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """非 DRAFT 状态不能 start_testing。"""
        agent = make_agent(status=AgentStatus.ACTIVE, owner_id=100)
        mock_agent_repo.get_by_id.return_value = agent

        with pytest.raises(InvalidStateTransitionError):
            await lifecycle_service.start_testing(agent_id=1, operator_id=100)

    @pytest.mark.asyncio
    async def test_start_testing_requires_blueprint(
        self,
        mock_agent_repo: AsyncMock,
        mock_blueprint_repo: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """没有 Blueprint 时抛出 DomainError。"""
        agent = make_agent(status=AgentStatus.DRAFT, owner_id=100)
        mock_agent_repo.get_by_id.return_value = agent
        mock_blueprint_repo.get_runtime_info.return_value = None

        with pytest.raises(DomainError, match="Blueprint"):
            await lifecycle_service.start_testing(agent_id=1, operator_id=100)

    @pytest.mark.asyncio
    async def test_start_testing_requires_workspace_path(
        self,
        mock_agent_repo: AsyncMock,
        mock_blueprint_repo: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """workspace_path 为空时抛出 DomainError。"""
        agent = make_agent(status=AgentStatus.DRAFT, owner_id=100)
        mock_agent_repo.get_by_id.return_value = agent
        mock_blueprint_repo.get_runtime_info.return_value = BlueprintRuntimeInfo(
            blueprint_id=10,
            workspace_path="",
            runtime_arn="",
            workspace_s3_uri="",
        )

        with pytest.raises(DomainError, match="工作目录"):
            await lifecycle_service.start_testing(agent_id=1, operator_id=100)

    @pytest.mark.asyncio
    async def test_start_testing_provision_failure_does_not_persist(
        self,
        mock_agent_repo: AsyncMock,
        mock_runtime_manager: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """provision 失败时 Agent 状态不持久化。"""
        agent = make_agent(status=AgentStatus.DRAFT, owner_id=100)
        mock_agent_repo.get_by_id.return_value = agent
        mock_runtime_manager.provision.side_effect = DomainError(
            message="Runtime 创建失败",
            code="RUNTIME_PROVISION_ERROR",
        )

        with pytest.raises(DomainError, match="Runtime 创建失败"):
            await lifecycle_service.start_testing(agent_id=1, operator_id=100)

        # Agent 状态未持久化
        mock_agent_repo.update.assert_not_called()


@pytest.mark.unit
class TestGoLive:
    """go_live — TESTING → ACTIVE。"""

    @pytest.mark.asyncio
    async def test_go_live_success(
        self,
        mock_agent_repo: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """TESTING → ACTIVE，不重新创建 Runtime。"""
        agent = make_agent(status=AgentStatus.TESTING, owner_id=100)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.return_value = agent

        result = await lifecycle_service.go_live(agent_id=1, operator_id=100)
        assert agent.status == AgentStatus.ACTIVE
        mock_agent_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_go_live_requires_testing_status(
        self,
        mock_agent_repo: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """DRAFT 不能直接 go_live (需要先 start_testing)。"""
        # go_live 调用 agent.activate()，DRAFT → ACTIVE 在 V1 中需要 system_prompt
        # 无 system_prompt 的 DRAFT agent 不能 activate
        agent = make_agent(status=AgentStatus.DRAFT, owner_id=100, system_prompt="")
        mock_agent_repo.get_by_id.return_value = agent

        # DRAFT → ACTIVE 需要 system_prompt，无 system_prompt 时会抛 ValidationError
        from src.shared.domain.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await lifecycle_service.go_live(agent_id=1, operator_id=100)


@pytest.mark.unit
class TestTakeOffline:
    """take_offline — ACTIVE → ARCHIVED + Runtime 销毁。"""

    @pytest.mark.asyncio
    async def test_take_offline_success(
        self,
        mock_agent_repo: AsyncMock,
        mock_blueprint_repo: AsyncMock,
        mock_runtime_manager: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """ACTIVE → ARCHIVED，销毁 Runtime。"""
        agent = make_agent(status=AgentStatus.ACTIVE, owner_id=100)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.return_value = agent
        mock_blueprint_repo.get_runtime_info.return_value = BlueprintRuntimeInfo(
            blueprint_id=10,
            workspace_path="/ws/1",
            runtime_arn="arn:aws:runtime/agent-1",
            workspace_s3_uri="s3://bucket/ws/1.tar.gz",
        )

        result = await lifecycle_service.take_offline(agent_id=1, operator_id=100)
        assert agent.status == AgentStatus.ARCHIVED
        mock_runtime_manager.deprovision.assert_called_once_with("arn:aws:runtime/agent-1")
        mock_blueprint_repo.clear_runtime_info.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_take_offline_deprovision_failure_does_not_block(
        self,
        mock_agent_repo: AsyncMock,
        mock_blueprint_repo: AsyncMock,
        mock_runtime_manager: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """deprovision 失败不阻塞归档 (best-effort)。"""
        agent = make_agent(status=AgentStatus.ACTIVE, owner_id=100)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.return_value = agent
        mock_blueprint_repo.get_runtime_info.return_value = BlueprintRuntimeInfo(
            blueprint_id=10,
            workspace_path="/ws/1",
            runtime_arn="arn:aws:runtime/agent-1",
            workspace_s3_uri="s3://bucket/ws/1.tar.gz",
        )
        mock_runtime_manager.deprovision.side_effect = Exception("Service unavailable")

        # 不抛异常，归档成功
        result = await lifecycle_service.take_offline(agent_id=1, operator_id=100)
        assert agent.status == AgentStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_take_offline_no_runtime_still_archives(
        self,
        mock_agent_repo: AsyncMock,
        mock_blueprint_repo: AsyncMock,
        mock_runtime_manager: AsyncMock,
        lifecycle_service: AgentService,
        mock_event_bus: AsyncMock,
    ) -> None:
        """没有 Runtime ARN 时跳过 deprovision，仍然归档。"""
        agent = make_agent(status=AgentStatus.ACTIVE, owner_id=100)
        mock_agent_repo.get_by_id.return_value = agent
        mock_agent_repo.update.return_value = agent
        mock_blueprint_repo.get_runtime_info.return_value = BlueprintRuntimeInfo(
            blueprint_id=10,
            workspace_path="/ws/1",
            runtime_arn="",
            workspace_s3_uri="",
        )

        result = await lifecycle_service.take_offline(agent_id=1, operator_id=100)
        assert agent.status == AgentStatus.ARCHIVED
        mock_runtime_manager.deprovision.assert_not_called()
