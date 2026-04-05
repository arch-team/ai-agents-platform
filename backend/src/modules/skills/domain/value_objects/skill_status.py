"""Skill 状态枚举。"""

from enum import StrEnum


class SkillStatus(StrEnum):
    """Skill 生命周期状态: DRAFT -> PUBLISHED -> ARCHIVED。"""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
