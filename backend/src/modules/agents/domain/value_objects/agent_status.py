"""Agent 状态枚举。"""

from enum import StrEnum


class AgentStatus(StrEnum):
    """Agent 生命周期状态。"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
