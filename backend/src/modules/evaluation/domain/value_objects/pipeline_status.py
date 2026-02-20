"""Pipeline 运行状态枚举。"""

from enum import StrEnum


class PipelineStatus(StrEnum):
    """Pipeline 运行状态: SCHEDULED -> RUNNING -> COMPLETED / FAILED。"""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
