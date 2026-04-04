"""Agent Blueprint 仓库接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class BlueprintRuntimeInfo:
    """Blueprint 运行时信息 — start_testing/take_offline 编排用。"""

    blueprint_id: int
    workspace_path: str
    runtime_arn: str
    workspace_s3_uri: str


class IAgentBlueprintRepository(ABC):
    """Agent Blueprint 仓库接口 — 聚焦 Runtime 生命周期编排所需的最小数据访问。"""

    @abstractmethod
    async def get_runtime_info(self, agent_id: int) -> BlueprintRuntimeInfo | None:
        """获取 Blueprint 的运行时信息 (workspace_path, runtime_arn 等)。"""

    @abstractmethod
    async def update_runtime_info(
        self,
        agent_id: int,
        *,
        runtime_arn: str,
        workspace_s3_uri: str,
    ) -> None:
        """更新 Blueprint 的 runtime_arn 和 workspace_s3_uri。"""

    @abstractmethod
    async def clear_runtime_info(self, agent_id: int) -> None:
        """清除 Blueprint 的 runtime_arn (归档时调用)。"""
