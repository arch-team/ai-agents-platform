"""评估运行领域实体。"""

from datetime import datetime

from pydantic import Field

from src.modules.evaluation.domain.value_objects.evaluation_run_status import EvaluationRunStatus
from src.shared.domain.base_entity import PydanticEntity, utc_now


class EvaluationRun(PydanticEntity):
    """评估运行实体，记录一次评估执行过程。"""

    suite_id: int
    agent_id: int
    user_id: int
    status: EvaluationRunStatus = EvaluationRunStatus.PENDING
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def start(self) -> None:
        """开始评估运行。PENDING -> RUNNING。"""
        self._require_status(self.status, EvaluationRunStatus.PENDING, EvaluationRunStatus.RUNNING.value)
        self.status = EvaluationRunStatus.RUNNING
        self.started_at = utc_now()
        self.touch()

    def complete(self, *, passed: int, failed: int, score: float) -> None:
        """完成评估运行。RUNNING -> COMPLETED。"""
        self._require_status(self.status, EvaluationRunStatus.RUNNING, EvaluationRunStatus.COMPLETED.value)
        self.status = EvaluationRunStatus.COMPLETED
        self.passed_cases = passed
        self.failed_cases = failed
        self.score = score
        self.completed_at = utc_now()
        self.touch()

    def fail(self) -> None:
        """标记评估运行失败。RUNNING -> FAILED。"""
        self._require_status(self.status, EvaluationRunStatus.RUNNING, EvaluationRunStatus.FAILED.value)
        self.status = EvaluationRunStatus.FAILED
        self.completed_at = utc_now()
        self.touch()
