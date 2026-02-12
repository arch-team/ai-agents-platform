"""评估运行状态枚举。"""

from enum import StrEnum


class EvaluationRunStatus(StrEnum):
    """评估运行状态: PENDING -> RUNNING -> COMPLETED / FAILED。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
