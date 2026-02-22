"""Builder 会话状态枚举。"""

from enum import StrEnum


class BuilderStatus(StrEnum):
    """Builder 会话生命周期状态。

    PENDING -> GENERATING -> CONFIRMED -> (confirm_creation 设置 agent_id)
    PENDING/GENERATING -> CANCELLED
    """

    PENDING = "pending"
    GENERATING = "generating"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
