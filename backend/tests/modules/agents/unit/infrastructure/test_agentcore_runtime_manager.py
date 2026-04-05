"""AgentCoreRuntimeManager 单元测试 — mock agentcore client。"""

from unittest.mock import MagicMock

import pytest

from src.modules.agents.application.interfaces.agent_runtime_manager import RuntimeInfo
from src.modules.agents.infrastructure.external.agentcore_runtime_manager import (
    AgentCoreRuntimeManager,
)
from src.shared.domain.exceptions import DomainError


@pytest.fixture
def mock_agentcore_client() -> MagicMock:
    """Mock bedrock-agentcore client。"""
    client = MagicMock()
    client.create_agent_runtime = MagicMock(
        return_value={
            "agentRuntimeArn": "arn:aws:bedrock-agentcore:us-east-1:123456:runtime/agent_42_dev",
            "agentRuntimeId": "rt-abc123",
        },
    )
    client.update_agent_runtime = MagicMock(return_value={})
    client.delete_agent_runtime = MagicMock(return_value={})
    return client


@pytest.fixture
def runtime_manager(mock_agentcore_client: MagicMock) -> AgentCoreRuntimeManager:
    """AgentCoreRuntimeManager 实例。"""
    return AgentCoreRuntimeManager(
        client=mock_agentcore_client,
        ecr_repo_uri="123456.dkr.ecr.us-east-1.amazonaws.com/agent-runtime",
        env_name="dev",
    )


@pytest.mark.unit
class TestProvision:
    """provision — 创建专属 Runtime。"""

    @pytest.mark.asyncio
    async def test_provision_creates_runtime_and_returns_info(
        self,
        runtime_manager: AgentCoreRuntimeManager,
        mock_agentcore_client: MagicMock,
    ) -> None:
        """正常创建 Runtime，返回 RuntimeInfo。"""
        result = await runtime_manager.provision(agent_id=42, workspace_s3_uri="s3://bucket/ws/42/workspace.tar.gz")

        assert isinstance(result, RuntimeInfo)
        assert result.runtime_arn == "arn:aws:bedrock-agentcore:us-east-1:123456:runtime/agent_42_dev"
        assert result.runtime_name == "agent-42-dev"

    @pytest.mark.asyncio
    async def test_provision_passes_correct_params(
        self,
        runtime_manager: AgentCoreRuntimeManager,
        mock_agentcore_client: MagicMock,
    ) -> None:
        """provision 传递正确的参数给 AgentCore API。"""
        await runtime_manager.provision(agent_id=42, workspace_s3_uri="s3://bucket/ws/42/workspace.tar.gz")

        mock_agentcore_client.create_agent_runtime.assert_called_once()
        call_kwargs = mock_agentcore_client.create_agent_runtime.call_args[1]

        assert call_kwargs["agentRuntimeName"] == "agent-42-dev"
        assert "ecr" in call_kwargs["agentRuntimeArtifact"]
        assert call_kwargs["agentRuntimeArtifact"]["ecr"]["repositoryUri"].endswith("/agent-runtime")
        assert call_kwargs["environmentVariables"]["WORKSPACE_S3_URI"] == "s3://bucket/ws/42/workspace.tar.gz"
        assert call_kwargs["environmentVariables"]["AGENT_ID"] == "42"

    @pytest.mark.asyncio
    async def test_provision_wraps_client_error_as_domain_error(
        self,
        runtime_manager: AgentCoreRuntimeManager,
        mock_agentcore_client: MagicMock,
    ) -> None:
        """AgentCore API 异常转换为 DomainError。"""
        mock_agentcore_client.create_agent_runtime.side_effect = Exception("ServiceUnavailable")

        with pytest.raises(DomainError, match="Runtime 创建失败"):
            await runtime_manager.provision(agent_id=42, workspace_s3_uri="s3://bucket/ws/42/workspace.tar.gz")


@pytest.mark.unit
class TestUpdateWorkspace:
    """update_workspace — 更新 Runtime Workspace。"""

    @pytest.mark.asyncio
    async def test_update_workspace_calls_update_api(
        self,
        runtime_manager: AgentCoreRuntimeManager,
        mock_agentcore_client: MagicMock,
    ) -> None:
        """调用 update_agent_runtime API 更新环境变量。"""
        arn = "arn:aws:bedrock-agentcore:us-east-1:123456:runtime/agent_42_dev"
        await runtime_manager.update_workspace(runtime_arn=arn, workspace_s3_uri="s3://bucket/ws/42/v2.tar.gz")

        mock_agentcore_client.update_agent_runtime.assert_called_once()
        call_kwargs = mock_agentcore_client.update_agent_runtime.call_args[1]
        assert call_kwargs["agentRuntimeArn"] == arn
        assert call_kwargs["environmentVariables"]["WORKSPACE_S3_URI"] == "s3://bucket/ws/42/v2.tar.gz"

    @pytest.mark.asyncio
    async def test_update_workspace_wraps_error(
        self,
        runtime_manager: AgentCoreRuntimeManager,
        mock_agentcore_client: MagicMock,
    ) -> None:
        """API 异常转换为 DomainError。"""
        mock_agentcore_client.update_agent_runtime.side_effect = Exception("Throttling")

        with pytest.raises(DomainError, match="Workspace 更新失败"):
            await runtime_manager.update_workspace(
                runtime_arn="arn:aws:test",
                workspace_s3_uri="s3://bucket/ws.tar.gz",
            )


@pytest.mark.unit
class TestDeprovision:
    """deprovision — 销毁 Runtime。"""

    @pytest.mark.asyncio
    async def test_deprovision_calls_delete_api(
        self,
        runtime_manager: AgentCoreRuntimeManager,
        mock_agentcore_client: MagicMock,
    ) -> None:
        """调用 delete_agent_runtime API。"""
        arn = "arn:aws:bedrock-agentcore:us-east-1:123456:runtime/agent_42_dev"
        await runtime_manager.deprovision(runtime_arn=arn)

        mock_agentcore_client.delete_agent_runtime.assert_called_once_with(agentRuntimeArn=arn)

    @pytest.mark.asyncio
    async def test_deprovision_wraps_error(
        self,
        runtime_manager: AgentCoreRuntimeManager,
        mock_agentcore_client: MagicMock,
    ) -> None:
        """API 异常转换为 DomainError。"""
        mock_agentcore_client.delete_agent_runtime.side_effect = Exception("ResourceNotFound")

        with pytest.raises(DomainError, match="Runtime 销毁失败"):
            await runtime_manager.deprovision(runtime_arn="arn:aws:test")
