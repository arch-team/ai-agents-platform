"""WorkspaceManager 实现 — 从 Blueprint 生成 Claude Code 可运行的工作目录。"""

import asyncio
import json
import shutil
import tarfile
from pathlib import Path

from src.modules.agents.application.interfaces.workspace_manager import (
    BlueprintDTO,
    IWorkspaceManager,
)


class WorkspaceManagerImpl(IWorkspaceManager):
    """基于本地文件系统 + S3 的 WorkspaceManager 实现。"""

    def __init__(self, *, workspace_root: Path, skill_library_root: Path, s3_bucket: str) -> None:
        self._workspace_root = workspace_root
        self._skill_library_root = skill_library_root
        self._s3_bucket = s3_bucket

    async def create_workspace(self, agent_id: int, blueprint: BlueprintDTO) -> Path:
        workspace = self._workspace_root / str(agent_id)
        claude_md = self._render_claude_md(blueprint)
        settings = self._render_settings(blueprint)
        settings_json = json.dumps(settings, ensure_ascii=False, indent=2)

        # 路径校验 (同步, 无 I/O)
        for skill_path in blueprint.skill_paths:
            self._validate_path(skill_path)

        # 文件系统操作委托到线程池, 避免阻塞事件循环
        await asyncio.to_thread(
            self._write_workspace_sync,
            workspace,
            claude_md,
            settings_json,
            blueprint.skill_paths,
        )
        return workspace

    async def upload_to_s3(self, workspace_path: Path, agent_id: int) -> str:
        return await asyncio.to_thread(self._upload_to_s3_sync, workspace_path, agent_id)

    async def update_workspace(self, agent_id: int, blueprint: BlueprintDTO) -> Path:
        workspace = self._workspace_root / str(agent_id)
        await asyncio.to_thread(shutil.rmtree, workspace, ignore_errors=True)
        return await self.create_workspace(agent_id, blueprint)

    # ── 同步文件操作 (由 asyncio.to_thread 调用) ──

    def _write_workspace_sync(
        self,
        workspace: Path,
        claude_md: str,
        settings_json: str,
        skill_paths: tuple[str, ...],
    ) -> None:
        """同步写入 workspace 文件。"""
        workspace.mkdir(parents=True, exist_ok=True)

        # 1. CLAUDE.md
        (workspace / "CLAUDE.md").write_text(claude_md, encoding="utf-8")

        # 2. Skills
        skills_dir = workspace / "skills"
        skills_dir.mkdir(exist_ok=True)
        for skill_path in skill_paths:
            self._copy_skill(skill_path, skills_dir)

        # 3. .claude/settings.json
        claude_dir = workspace / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "settings.json").write_text(settings_json, encoding="utf-8")

    def _upload_to_s3_sync(self, workspace_path: Path, agent_id: int) -> str:
        """同步 tar 打包 (实际 S3 上传待集成时实现)。"""
        tar_name = "workspace.tar.gz"
        tar_path = workspace_path.parent / f"{agent_id}_{tar_name}"
        try:
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(workspace_path, arcname=".")
            s3_key = f"agent-workspaces/{agent_id}/{tar_name}"
            return f"s3://{self._s3_bucket}/{s3_key}"
        finally:
            tar_path.unlink(missing_ok=True)

    def _render_claude_md(self, blueprint: BlueprintDTO) -> str:
        """生成 CLAUDE.md — Agent 的角色定义、行为规则和安全边界。"""
        sections: list[str] = []

        # 角色定义
        sections.append(f"# {blueprint.persona_role}\n\n{blueprint.persona_background}")

        if blueprint.persona_tone:
            sections.append(f"\n## 沟通风格\n{blueprint.persona_tone}")

        # 安全护栏
        if blueprint.guardrails:
            lines = ["\n## 安全边界(必须遵守)"]
            for g in blueprint.guardrails:
                prefix = "⛔" if g.severity == "block" else "⚠️"
                lines.append(f"- {prefix} {g.rule}")
            sections.append("\n".join(lines))

        # 记忆策略
        if blueprint.memory_enabled and blueprint.memory_retain_fields:
            fields = "、".join(blueprint.memory_retain_fields)
            sections.append(f"\n## 记忆策略\n请记住: {fields}")

        return "\n".join(sections)

    def _render_settings(self, blueprint: BlueprintDTO) -> dict[str, object]:
        """生成 .claude/settings.json — MCP 工具配置占位。"""
        return {
            "tools": [{"name": tb.display_name, "hint": tb.usage_hint} for tb in blueprint.tool_bindings],
        }

    def _copy_skill(self, skill_relative_path: str, target_skills_dir: Path) -> None:
        """将 Skill 从 library 复制到 workspace/skills/。"""
        source = self._skill_library_root / skill_relative_path
        # 提取 skill 名称 (路径的倒数第二级目录)
        # e.g. "published/return-processing/v1" → "return-processing"
        parts = Path(skill_relative_path).parts
        skill_name = parts[-2] if len(parts) >= 2 else parts[-1]
        target = target_skills_dir / skill_name
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(source, target)

    def _validate_path(self, path: str) -> None:
        """路径安全校验 — 拒绝路径遍历、绝对路径和符号链接。"""
        if path.startswith("/"):
            msg = f"路径安全校验失败: 不允许绝对路径 '{path}'"
            raise ValueError(msg)
        if ".." in Path(path).parts:
            msg = f"路径安全校验失败: 不允许路径遍历 '{path}'"
            raise ValueError(msg)
        # 加固: resolve 后确认仍在 skill_library_root 下 (防止符号链接逃逸)
        resolved = (self._skill_library_root / path).resolve()
        if not resolved.is_relative_to(self._skill_library_root.resolve()):
            msg = f"路径安全校验失败: 解析后路径逃逸根目录 '{path}'"
            raise ValueError(msg)
