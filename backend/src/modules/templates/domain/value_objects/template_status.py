"""模板状态枚举。"""

from enum import StrEnum


class TemplateStatus(StrEnum):
    """模板生命周期状态: DRAFT -> PUBLISHED -> ARCHIVED。"""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
