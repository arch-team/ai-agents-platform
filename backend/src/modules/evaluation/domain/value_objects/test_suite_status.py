"""测试集状态枚举。"""

from enum import StrEnum


class TestSuiteStatus(StrEnum):
    """测试集生命周期状态: DRAFT -> ACTIVE -> ARCHIVED。"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
