"""Agent 状态枚举。"""

from enum import StrEnum


class AgentStatus(StrEnum):
    """Agent 状态枚举。"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
