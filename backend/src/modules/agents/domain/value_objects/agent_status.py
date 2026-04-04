"""Agent 状态枚举。"""

from enum import StrEnum


class AgentStatus(StrEnum):
    """Agent 生命周期状态。

    状态机: DRAFT → TESTING → ACTIVE → ARCHIVED
    V1 兼容: DRAFT → ACTIVE (无 Blueprint 时直通)
    """

    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    ARCHIVED = "archived"
