"""WorkspaceManager 单元测试。"""

import json
from pathlib import Path

import pytest

from src.modules.agents.application.interfaces.workspace_manager import (
    BlueprintDTO,
    GuardrailDTO,
    ToolBindingDTO,
)
from src.modules.agents.infrastructure.external.workspace_manager import WorkspaceManagerImpl


def _make_blueprint(**kwargs: object) -> BlueprintDTO:
    """创建测试用 Blueprint DTO。"""
    defaults: dict[str, object] = {
        "agent_name": "退货客服助手",
        "persona_role": "安克售后客服专员",
        "persona_background": "负责处理退货和换货业务，熟悉安克全线产品的售后政策。",
        "persona_tone": "专业且友善",
        "guardrails": (
            GuardrailDTO(rule="不能承诺超出政策的退款", severity="block"),
            GuardrailDTO(rule="不能泄露其他客户信息", severity="warn"),
        ),
        "memory_enabled": True,
        "memory_retain_fields": ("订单号", "客户诉求"),
        "skill_paths": (),
        "tool_bindings": (ToolBindingDTO(display_name="订单查询", usage_hint="查询客户订单状态"),),
    }
    defaults.update(kwargs)
    return BlueprintDTO(**defaults)  # type: ignore[arg-type]


@pytest.mark.unit
class TestWorkspaceManagerCreateWorkspace:
    """测试 create_workspace 生成正确的目录结构。"""

    @pytest.fixture
    def workspace_root(self, tmp_path: Path) -> Path:
        return tmp_path / "agent-workspaces"

    @pytest.fixture
    def skill_library_root(self, tmp_path: Path) -> Path:
        lib = tmp_path / "skill-library"
        lib.mkdir()
        return lib

    @pytest.fixture
    def manager(self, workspace_root: Path, skill_library_root: Path) -> WorkspaceManagerImpl:
        return WorkspaceManagerImpl(
            workspace_root=workspace_root,
            skill_library_root=skill_library_root,
            s3_bucket="test-bucket",
        )

    @pytest.mark.asyncio
    async def test_creates_workspace_directory(self, manager: WorkspaceManagerImpl, workspace_root: Path) -> None:
        blueprint = _make_blueprint()
        result = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        assert result == workspace_root / "42"
        assert result.is_dir()

    @pytest.mark.asyncio
    async def test_generates_claude_md(self, manager: WorkspaceManagerImpl) -> None:
        blueprint = _make_blueprint()
        workspace = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        claude_md = (workspace / "CLAUDE.md").read_text(encoding="utf-8")
        # 验证角色信息
        assert "安克售后客服专员" in claude_md
        assert "负责处理退货和换货业务" in claude_md

    @pytest.mark.asyncio
    async def test_claude_md_contains_tone(self, manager: WorkspaceManagerImpl) -> None:
        blueprint = _make_blueprint(persona_tone="专业且友善")
        workspace = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        claude_md = (workspace / "CLAUDE.md").read_text(encoding="utf-8")
        assert "专业且友善" in claude_md

    @pytest.mark.asyncio
    async def test_claude_md_contains_guardrails(self, manager: WorkspaceManagerImpl) -> None:
        blueprint = _make_blueprint()
        workspace = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        claude_md = (workspace / "CLAUDE.md").read_text(encoding="utf-8")
        assert "不能承诺超出政策的退款" in claude_md
        assert "不能泄露其他客户信息" in claude_md
        # block 级别用 ⛔, warn 级别用 ⚠️
        assert "⛔" in claude_md
        assert "⚠️" in claude_md

    @pytest.mark.asyncio
    async def test_claude_md_contains_memory_config(self, manager: WorkspaceManagerImpl) -> None:
        blueprint = _make_blueprint(memory_enabled=True, memory_retain_fields=("订单号",))
        workspace = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        claude_md = (workspace / "CLAUDE.md").read_text(encoding="utf-8")
        assert "订单号" in claude_md

    @pytest.mark.asyncio
    async def test_creates_skills_directory(self, manager: WorkspaceManagerImpl) -> None:
        blueprint = _make_blueprint(skill_paths=())
        workspace = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        assert (workspace / "skills").is_dir()

    @pytest.mark.asyncio
    async def test_copies_skill_from_library(
        self,
        manager: WorkspaceManagerImpl,
        skill_library_root: Path,
    ) -> None:
        # 准备 Skill 库中的 Skill
        skill_dir = skill_library_root / "published" / "return-processing" / "v1"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: 退货处理\n---\n", encoding="utf-8")

        blueprint = _make_blueprint(
            skill_paths=("published/return-processing/v1",),
        )
        workspace = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        copied_skill = workspace / "skills" / "return-processing" / "SKILL.md"
        assert copied_skill.exists()
        assert "退货处理" in copied_skill.read_text(encoding="utf-8")

    @pytest.mark.asyncio
    async def test_creates_claude_settings(self, manager: WorkspaceManagerImpl) -> None:
        blueprint = _make_blueprint(
            tool_bindings=(ToolBindingDTO(display_name="订单查询"),),
        )
        workspace = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        settings_path = workspace / ".claude" / "settings.json"
        assert settings_path.exists()
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert isinstance(settings, dict)

    @pytest.mark.asyncio
    async def test_idempotent_create(self, manager: WorkspaceManagerImpl) -> None:
        blueprint = _make_blueprint()
        path1 = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        path2 = await manager.create_workspace(agent_id=42, blueprint=blueprint)
        assert path1 == path2
        assert path1.is_dir()


@pytest.mark.unit
class TestWorkspaceManagerPathSafety:
    """路径安全校验 — 防止路径遍历。"""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> WorkspaceManagerImpl:
        return WorkspaceManagerImpl(
            workspace_root=tmp_path / "workspaces",
            skill_library_root=tmp_path / "skill-library",
            s3_bucket="test-bucket",
        )

    @pytest.mark.asyncio
    async def test_rejects_path_traversal_in_skill_path(self, manager: WorkspaceManagerImpl) -> None:
        blueprint = _make_blueprint(skill_paths=("../../etc/passwd",))
        with pytest.raises(ValueError, match="路径"):
            await manager.create_workspace(agent_id=42, blueprint=blueprint)

    @pytest.mark.asyncio
    async def test_rejects_absolute_skill_path(self, manager: WorkspaceManagerImpl) -> None:
        blueprint = _make_blueprint(skill_paths=("/etc/passwd",))
        with pytest.raises(ValueError, match="路径"):
            await manager.create_workspace(agent_id=42, blueprint=blueprint)


@pytest.mark.unit
class TestWorkspaceManagerUploadToS3:
    """S3 上传测试 (mock boto3)。"""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> WorkspaceManagerImpl:
        return WorkspaceManagerImpl(
            workspace_root=tmp_path / "workspaces",
            skill_library_root=tmp_path / "skill-library",
            s3_bucket="my-workspace-bucket",
        )

    @pytest.mark.asyncio
    async def test_upload_returns_s3_uri(self, manager: WorkspaceManagerImpl, tmp_path: Path) -> None:
        workspace = tmp_path / "workspaces" / "42"
        workspace.mkdir(parents=True)
        (workspace / "CLAUDE.md").write_text("# Agent", encoding="utf-8")

        uri = await manager.upload_to_s3(workspace_path=workspace, agent_id=42)
        assert uri.startswith("s3://my-workspace-bucket/")
        assert "42" in uri
        assert uri.endswith(".tar.gz")
