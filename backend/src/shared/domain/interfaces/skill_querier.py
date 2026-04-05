"""Skill 跨模块查询接口 — 供 agents/builder 等模块使用。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SkillInfo:
    """已发布 Skill 的最小信息集。"""

    id: int
    name: str
    description: str
    category: str
    trigger_description: str
    version: int
    file_path: str


@dataclass(frozen=True)
class SkillSummary:
    """Skill 摘要 (列表展示用)。"""

    id: int
    name: str
    description: str
    category: str


class ISkillQuerier(ABC):
    """Skill 跨模块查询接口。"""

    @abstractmethod
    async def get_published_skills(self, skill_ids: list[int]) -> list[SkillInfo]:
        """批量获取已发布的 Skill 信息。"""

    @abstractmethod
    async def list_published_skills(self, *, category: str | None = None, limit: int = 20) -> list[SkillSummary]:
        """列出已发布的 Skill 摘要。"""
