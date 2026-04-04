"""Skill 相关 DTO。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateSkillDTO:
    """创建 Skill 请求数据。"""

    name: str
    description: str = ""
    category: str = "general"
    trigger_description: str = ""
    skill_md: str = ""
    references: dict[str, str] | None = None


@dataclass
class UpdateSkillDTO:
    """更新 Skill 请求数据。"""

    name: str | None = None
    description: str | None = None
    category: str | None = None
    trigger_description: str | None = None
    skill_md: str | None = None
    references: dict[str, str] | None = None


@dataclass
class SkillDTO:
    """Skill 响应数据。"""

    id: int
    name: str
    description: str
    category: str
    trigger_description: str
    status: str
    creator_id: int
    version: int
    usage_count: int
    file_path: str
    created_at: datetime
    updated_at: datetime
