"""Skill 文件系统操作接口 (Infrastructure 层实现)。"""

from abc import ABC, abstractmethod


class ISkillFileManager(ABC):
    """Skill 文件系统操作抽象。

    职责: SKILL.md 的读写、草稿 → 发布的版本化复制、工作目录链接。
    数据库只存元信息，SKILL.md 内容由此接口管理。
    """

    @abstractmethod
    async def save_draft(self, skill_name: str, skill_md: str, references: dict[str, str] | None = None) -> str:
        """保存 Skill 草稿到文件系统。

        Returns:
            草稿目录的相对路径 (如 "drafts/{skill_name}")
        """

    @abstractmethod
    async def publish(self, draft_path: str, skill_name: str, version: int) -> str:
        """将草稿发布为指定版本（版本化复制）。

        Returns:
            已发布目录的相对路径 (如 "published/{skill_name}/v{version}")
        """

    @abstractmethod
    async def read_skill_md(self, file_path: str) -> str:
        """读取 SKILL.md 内容。

        Raises:
            FileNotFoundError: 文件不存在
        """

    @abstractmethod
    async def update_draft(self, draft_path: str, skill_md: str, references: dict[str, str] | None = None) -> None:
        """更新已有草稿的 SKILL.md 内容。"""

    @abstractmethod
    async def delete_draft(self, draft_path: str) -> None:
        """删除草稿目录及其所有内容。"""

    @abstractmethod
    async def copy_to_workspace(self, published_path: str, workspace_skills_dir: str, skill_name: str) -> None:
        """将已发布的 Skill 版本化复制到 Agent workspace 的 skills/ 目录。"""
