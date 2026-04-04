"""Agent Runtime 生命周期管理接口 (Infrastructure 层实现)。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeInfo:
    """Runtime 创建结果 — 包含 ARN 和名称。"""

    runtime_arn: str
    runtime_name: str


class IAgentRuntimeManager(ABC):
    """Agent Runtime 生命周期管理。

    职责:
    - provision: 创建专属 AgentCore Runtime (DRAFT → TESTING 时调用)
    - update_workspace: 更新 Runtime 的 Workspace (Skill 变更时调用)
    - deprovision: 销毁 Runtime (ACTIVE → ARCHIVED 时调用)
    """

    @abstractmethod
    async def provision(self, agent_id: int, workspace_s3_uri: str) -> RuntimeInfo:
        """创建专属 AgentCore Runtime。

        Raises:
            DomainError: Runtime 创建失败
        """

    @abstractmethod
    async def update_workspace(self, runtime_arn: str, workspace_s3_uri: str) -> None:
        """更新 Runtime 的 Workspace (Skill 变更 / 容器滚动更新)。

        Raises:
            DomainError: 更新失败
        """

    @abstractmethod
    async def deprovision(self, runtime_arn: str) -> None:
        """销毁 Runtime，释放资源。

        Raises:
            DomainError: 销毁失败
        """
