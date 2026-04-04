"""SkillFileManagerImpl 单元测试 — 使用 tmp_path 替代真实文件系统。"""

from pathlib import Path

import pytest

from src.modules.skills.infrastructure.external.skill_file_manager_impl import SkillFileManagerImpl


SAMPLE_SKILL_MD = """\
---
name: return-processing
description: 处理客户退货咨询。当客户提到退货、退款时使用。
---

## 流程步骤

1. 确认客户身份
2. 检查退货条件
3. 生成退货单
"""


@pytest.fixture
def manager(tmp_path: Path) -> SkillFileManagerImpl:
    """创建使用临时目录的 SkillFileManagerImpl。"""
    return SkillFileManagerImpl(workspace_root=tmp_path)


@pytest.mark.unit
class TestSaveDraft:
    """save_draft: 保存 SKILL.md 草稿。"""

    @pytest.mark.asyncio
    async def test_save_draft_creates_skill_md(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        path = await manager.save_draft("return-processing", SAMPLE_SKILL_MD)
        skill_md_file = tmp_path / path / "SKILL.md"
        assert skill_md_file.exists()
        assert "return-processing" in skill_md_file.read_text()

    @pytest.mark.asyncio
    async def test_save_draft_returns_relative_path(self, manager: SkillFileManagerImpl) -> None:
        path = await manager.save_draft("order-inquiry", SAMPLE_SKILL_MD)
        assert path == "drafts/order-inquiry"

    @pytest.mark.asyncio
    async def test_save_draft_with_references(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        refs = {"policy-guide.md": "# 退货政策\n\n30 天无理由退货。"}
        path = await manager.save_draft("return-processing", SAMPLE_SKILL_MD, references=refs)
        refs_dir = tmp_path / path / "references"
        assert refs_dir.exists()
        assert (refs_dir / "policy-guide.md").read_text() == "# 退货政策\n\n30 天无理由退货。"
        assert (refs_dir / "_index.yml").exists()

    @pytest.mark.asyncio
    async def test_save_draft_overwrites_existing(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        await manager.save_draft("test-skill", "旧内容")
        await manager.save_draft("test-skill", "新内容")
        content = (tmp_path / "drafts" / "test-skill" / "SKILL.md").read_text()
        assert "新内容" in content


@pytest.mark.unit
class TestPublish:
    """publish: 草稿 → 已发布版本化复制。"""

    @pytest.mark.asyncio
    async def test_publish_creates_versioned_directory(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        await manager.save_draft("return-processing", SAMPLE_SKILL_MD)
        pub_path = await manager.publish("drafts/return-processing", "return-processing", version=1)
        assert pub_path == "published/return-processing/v1"
        assert (tmp_path / pub_path / "SKILL.md").exists()

    @pytest.mark.asyncio
    async def test_publish_copies_references(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        refs = {"policy.md": "退货政策内容"}
        await manager.save_draft("return-processing", SAMPLE_SKILL_MD, references=refs)
        pub_path = await manager.publish("drafts/return-processing", "return-processing", version=1)
        assert (tmp_path / pub_path / "references" / "policy.md").exists()

    @pytest.mark.asyncio
    async def test_publish_multiple_versions(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        await manager.save_draft("test-skill", "版本 1 内容")
        await manager.publish("drafts/test-skill", "test-skill", version=1)
        await manager.save_draft("test-skill", "版本 2 内容")
        await manager.publish("drafts/test-skill", "test-skill", version=2)
        assert (tmp_path / "published" / "test-skill" / "v1" / "SKILL.md").exists()
        assert (tmp_path / "published" / "test-skill" / "v2" / "SKILL.md").exists()


@pytest.mark.unit
class TestReadSkillMd:
    """read_skill_md: 读取 SKILL.md 内容。"""

    @pytest.mark.asyncio
    async def test_read_existing_skill_md(self, manager: SkillFileManagerImpl) -> None:
        path = await manager.save_draft("test-skill", SAMPLE_SKILL_MD)
        content = await manager.read_skill_md(path)
        assert "return-processing" in content

    @pytest.mark.asyncio
    async def test_read_nonexistent_raises(self, manager: SkillFileManagerImpl) -> None:
        with pytest.raises(FileNotFoundError):
            await manager.read_skill_md("nonexistent/path")


@pytest.mark.unit
class TestUpdateDraft:
    """update_draft: 更新已有草稿内容。"""

    @pytest.mark.asyncio
    async def test_update_draft_overwrites_content(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        path = await manager.save_draft("test-skill", "旧内容")
        await manager.update_draft(path, "新内容")
        content = (tmp_path / path / "SKILL.md").read_text()
        assert "新内容" in content

    @pytest.mark.asyncio
    async def test_update_draft_replaces_references(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        old_refs = {"old.md": "旧参考"}
        await manager.save_draft("test-skill", "内容", references=old_refs)
        new_refs = {"new.md": "新参考"}
        await manager.update_draft("drafts/test-skill", "新内容", references=new_refs)
        refs_dir = tmp_path / "drafts" / "test-skill" / "references"
        assert not (refs_dir / "old.md").exists()
        assert (refs_dir / "new.md").read_text() == "新参考"


@pytest.mark.unit
class TestDeleteDraft:
    """delete_draft: 删除草稿目录。"""

    @pytest.mark.asyncio
    async def test_delete_removes_directory(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        path = await manager.save_draft("test-skill", "内容")
        await manager.delete_draft(path)
        assert not (tmp_path / path).exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_is_noop(self, manager: SkillFileManagerImpl) -> None:
        await manager.delete_draft("nonexistent/path")


@pytest.mark.unit
class TestCopyToWorkspace:
    """copy_to_workspace: 版本化复制到 Agent workspace。"""

    @pytest.mark.asyncio
    async def test_copy_to_workspace(self, manager: SkillFileManagerImpl, tmp_path: Path) -> None:
        await manager.save_draft("return-processing", SAMPLE_SKILL_MD)
        pub_path = await manager.publish("drafts/return-processing", "return-processing", version=1)
        workspace_dir = str(tmp_path / "agent-workspaces" / "agent-1" / "skills")
        await manager.copy_to_workspace(pub_path, workspace_dir, "return-processing")
        target = Path(workspace_dir) / "return-processing" / "SKILL.md"
        assert target.exists()
        assert "return-processing" in target.read_text()


@pytest.mark.unit
class TestPathSafety:
    """路径安全校验 — 防止路径遍历攻击。"""

    @pytest.mark.asyncio
    async def test_reject_path_traversal_in_skill_name(self, manager: SkillFileManagerImpl) -> None:
        with pytest.raises(ValueError, match="非法"):
            await manager.save_draft("../../../etc/passwd", "恶意内容")

    @pytest.mark.asyncio
    async def test_reject_absolute_path_in_skill_name(self, manager: SkillFileManagerImpl) -> None:
        with pytest.raises(ValueError, match="非法"):
            await manager.save_draft("/etc/passwd", "恶意内容")
