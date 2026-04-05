"""Agent 工作目录管理接口 (Infrastructure 层实现)。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BlueprintDTO:
    """WorkspaceManager 用的 Blueprint 数据传输对象。"""

    agent_name: str
    persona_role: str
    persona_background: str
    persona_tone: str = ""
    guardrails: tuple["GuardrailDTO", ...] = ()
    memory_enabled: bool = False
    memory_retain_fields: tuple[str, ...] = ()
    skill_paths: tuple[str, ...] = ()
    tool_bindings: tuple["ToolBindingDTO", ...] = ()


@dataclass(frozen=True)
class GuardrailDTO:
    """护栏规则 DTO。"""

    rule: str
    severity: str = "warn"


@dataclass(frozen=True)
class ToolBindingDTO:
    """工具绑定 DTO。"""

    display_name: str
    usage_hint: str = ""


class IWorkspaceManager(ABC):
    """Agent 工作目录管理器 — 从 Blueprint 生成 Claude Code 可运行的目录。

    职责:
    - create_workspace: 生成 CLAUDE.md + skills/ + .claude/settings.json
    - upload_to_s3: 打包上传到 S3
    - update_workspace: 重新生成 + 重新上传
    """

    @abstractmethod
    async def create_workspace(self, agent_id: int, blueprint: BlueprintDTO) -> Path:
        """根据 Blueprint 创建 Agent 工作目录。

        Returns:
            工作目录的绝对路径
        """

    @abstractmethod
    async def upload_to_s3(self, workspace_path: Path, agent_id: int) -> str:
        """将工作目录打包上传到 S3。

        Returns:
            S3 URI (如 s3://bucket/agent-workspaces/1/workspace.tar.gz)
        """

    @abstractmethod
    async def update_workspace(self, agent_id: int, blueprint: BlueprintDTO) -> Path:
        """重新生成工作目录（先清理旧目录再创建）。

        Returns:
            工作目录的绝对路径
        """
