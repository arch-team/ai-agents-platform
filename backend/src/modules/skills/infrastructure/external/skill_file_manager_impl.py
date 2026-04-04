"""Skill 文件系统操作实现 — pathlib 同步 I/O (SKILL.md 为小文件)。"""

import shutil
from pathlib import Path

from src.modules.skills.application.interfaces.skill_file_manager import ISkillFileManager


class SkillFileManagerImpl(ISkillFileManager):
    """基于本地文件系统的 Skill 文件管理器。

    目录布局:
      {workspace_root}/drafts/{skill_name}/SKILL.md
      {workspace_root}/published/{skill_name}/v{N}/SKILL.md
    """

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root

    # ── 公开方法 ──

    async def save_draft(self, skill_name: str, skill_md: str, references: dict[str, str] | None = None) -> str:
        self._validate_name(skill_name)
        rel_path = f"drafts/{skill_name}"
        draft_dir = self._root / rel_path
        draft_dir.mkdir(parents=True, exist_ok=True)
        self._write_file(draft_dir / "SKILL.md", skill_md)
        if references:
            self._write_references(draft_dir / "references", references)
        return rel_path

    async def publish(self, draft_path: str, skill_name: str, version: int) -> str:
        self._validate_name(skill_name)
        src_dir = self._root / draft_path
        rel_path = f"published/{skill_name}/v{version}"
        dest_dir = self._root / rel_path
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(src_dir, dest_dir)
        return rel_path

    async def read_skill_md(self, file_path: str) -> str:
        skill_md = self._root / file_path / "SKILL.md"
        if not skill_md.exists():
            msg = f"SKILL.md 不存在: {file_path}"
            raise FileNotFoundError(msg)
        return skill_md.read_text(encoding="utf-8")

    async def update_draft(self, draft_path: str, skill_md: str, references: dict[str, str] | None = None) -> None:
        draft_dir = self._root / draft_path
        self._write_file(draft_dir / "SKILL.md", skill_md)
        if references is not None:
            refs_dir = draft_dir / "references"
            if refs_dir.exists():
                shutil.rmtree(refs_dir)
            self._write_references(refs_dir, references)

    async def delete_draft(self, draft_path: str) -> None:
        target = self._root / draft_path
        if target.exists():
            shutil.rmtree(target)

    async def copy_to_workspace(self, published_path: str, workspace_skills_dir: str, skill_name: str) -> None:
        self._validate_name(skill_name)
        src_dir = self._root / published_path
        dest_dir = Path(workspace_skills_dir) / skill_name
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(src_dir, dest_dir)

    # ── 内部辅助 ──

    @staticmethod
    def _validate_name(name: str) -> None:
        """路径安全校验 — 防止路径遍历。"""
        if ".." in name or name.startswith(("/", "\\")):
            msg = f"非法的 Skill 名称: {name}"
            raise ValueError(msg)

    @staticmethod
    def _write_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_references(self, refs_dir: Path, references: dict[str, str]) -> None:
        refs_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in references.items():
            self._validate_name(filename)
            self._write_file(refs_dir / filename, content)
        # 生成 _index.yml
        index_lines = [f"- {filename}" for filename in references]
        self._write_file(refs_dir / "_index.yml", "\n".join(index_lines) + "\n")
