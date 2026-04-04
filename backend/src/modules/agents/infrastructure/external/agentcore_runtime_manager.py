"""AgentCore Runtime 生命周期管理实现。

SDK-First: 薄封装层，通过 bedrock-agentcore SDK 动态创建/更新/销毁
Agent 专属 Runtime。每个上线 Agent 拥有独立 Runtime 容器。

架构:
  AgentService → AgentCoreRuntimeManager → boto3 AgentCore API
                                           ├── create_agent_runtime (TESTING)
                                           ├── update_agent_runtime (Skill 变更)
                                           └── delete_agent_runtime (ARCHIVED)
"""

import asyncio
from typing import Any, Protocol

import structlog

from src.modules.agents.application.interfaces.agent_runtime_manager import (
    IAgentRuntimeManager,
    RuntimeInfo,
)
from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


class _AgentCoreControlClient(Protocol):
    """boto3 bedrock-agentcore control client 最小协议。"""

    def create_agent_runtime(self, **kwargs: Any) -> dict[str, Any]: ...
    def update_agent_runtime(self, **kwargs: Any) -> dict[str, Any]: ...
    def delete_agent_runtime(self, **kwargs: Any) -> dict[str, Any]: ...


class AgentCoreRuntimeManager(IAgentRuntimeManager):
    """通过 AgentCore API 动态管理 Agent Runtime。

    每个 Agent 在 TESTING 阶段获得专属 Runtime 容器，
    ACTIVE 阶段复用同一容器，ARCHIVED 阶段销毁释放资源。
    """

    def __init__(self, *, client: _AgentCoreControlClient, ecr_repo_uri: str, env_name: str) -> None:
        self._client = client
        self._ecr_repo_uri = ecr_repo_uri
        self._env_name = env_name

    async def provision(self, agent_id: int, workspace_s3_uri: str) -> RuntimeInfo:
        """创建专属 AgentCore Runtime。"""
        runtime_name = f"agent-{agent_id}-{self._env_name}"

        try:
            response = await asyncio.to_thread(
                self._client.create_agent_runtime,
                agentRuntimeName=runtime_name,
                agentRuntimeArtifact={
                    "ecr": {
                        "repositoryUri": self._ecr_repo_uri,
                        "tag": "latest",
                    },
                },
                environmentVariables={
                    "WORKSPACE_S3_URI": workspace_s3_uri,
                    "AGENT_ID": str(agent_id),
                    "ENV_NAME": self._env_name,
                },
            )
        except Exception as e:
            logger.exception("agentcore_runtime_provision_failed", agent_id=agent_id)
            raise DomainError(
                message=f"Runtime 创建失败: {e}",
                code="RUNTIME_PROVISION_ERROR",
            ) from e

        runtime_arn = response["agentRuntimeArn"]
        logger.info("agentcore_runtime_provisioned", agent_id=agent_id, runtime_arn=runtime_arn)

        return RuntimeInfo(runtime_arn=runtime_arn, runtime_name=runtime_name)

    async def update_workspace(self, runtime_arn: str, workspace_s3_uri: str) -> None:
        """更新 Runtime 的 Workspace (Skill 变更 / 容器滚动更新)。"""
        try:
            await asyncio.to_thread(
                self._client.update_agent_runtime,
                agentRuntimeArn=runtime_arn,
                environmentVariables={
                    "WORKSPACE_S3_URI": workspace_s3_uri,
                },
            )
        except Exception as e:
            logger.exception("agentcore_runtime_update_failed", runtime_arn=runtime_arn)
            raise DomainError(
                message=f"Workspace 更新失败: {e}",
                code="RUNTIME_UPDATE_ERROR",
            ) from e

        logger.info("agentcore_runtime_workspace_updated", runtime_arn=runtime_arn)

    async def deprovision(self, runtime_arn: str) -> None:
        """销毁 Runtime，释放资源。"""
        try:
            await asyncio.to_thread(
                self._client.delete_agent_runtime,
                agentRuntimeArn=runtime_arn,
            )
        except Exception as e:
            logger.exception("agentcore_runtime_deprovision_failed", runtime_arn=runtime_arn)
            raise DomainError(
                message=f"Runtime 销毁失败: {e}",
                code="RUNTIME_DEPROVISION_ERROR",
            ) from e

        logger.info("agentcore_runtime_deprovisioned", runtime_arn=runtime_arn)
