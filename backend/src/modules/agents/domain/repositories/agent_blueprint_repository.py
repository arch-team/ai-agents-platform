"""Agent Blueprint 仓库接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BlueprintRuntimeInfo:
    """Blueprint 运行时信息 — start_testing/take_offline 编排用。"""

    blueprint_id: int
    workspace_path: str
    runtime_arn: str
    workspace_s3_uri: str


@dataclass
class CreateBlueprintDTO:
    """创建 Blueprint 的数据传输对象。"""

    agent_id: int
    persona_config: str = "{}"
    memory_config: str = "{}"
    guardrails: str = "[]"
    model_config_json: str = "{}"
    knowledge_base_ids: str = "[]"
    workspace_path: str = ""
    skill_ids: list[int] = field(default_factory=list)
    tool_bindings: list["CreateToolBindingDTO"] = field(default_factory=list)


@dataclass(frozen=True)
class CreateToolBindingDTO:
    """创建工具绑定的数据传输对象。"""

    tool_id: int
    display_name: str
    usage_hint: str = ""


class IAgentBlueprintRepository(ABC):
    """Agent Blueprint 仓库接口。"""

    @abstractmethod
    async def create_blueprint(self, dto: CreateBlueprintDTO) -> int:
        """创建 Blueprint 记录 + 关联的 skills 和 tool_bindings。

        Returns:
            新创建的 Blueprint ID
        """

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
    async def update_workspace_path(self, agent_id: int, workspace_path: str) -> None:
        """更新 Blueprint 的 workspace_path。"""

    @abstractmethod
    async def clear_runtime_info(self, agent_id: int) -> None:
        """清除 Blueprint 的 runtime_arn (归档时调用)。"""
