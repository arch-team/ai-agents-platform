"""团队执行状态枚举。"""

from enum import StrEnum


class TeamExecutionStatus(StrEnum):
    """团队执行状态。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
