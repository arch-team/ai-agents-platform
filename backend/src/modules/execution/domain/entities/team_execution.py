"""团队执行实体。"""

from datetime import datetime

from pydantic import Field

from src.modules.execution.domain.value_objects.team_execution_status import (
    TeamExecutionStatus,
)
from src.shared.domain.base_entity import PydanticEntity, utc_now


class TeamExecution(PydanticEntity):
    """团队执行实体，表示一次 Agent 团队任务执行。"""

    agent_id: int
    user_id: int
    conversation_id: int | None = None
    prompt: str = Field(max_length=100000)
    status: TeamExecutionStatus = TeamExecutionStatus.PENDING
    result: str = ""
    error_message: str = ""
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def start(self) -> None:
        """启动执行。PENDING -> RUNNING。"""
        self._require_status(
            self.status,
            TeamExecutionStatus.PENDING,
            TeamExecutionStatus.RUNNING.value,
        )
        self.status = TeamExecutionStatus.RUNNING
        self.started_at = utc_now()
        self.touch()

    def complete(
        self,
        result: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """完成执行。RUNNING -> COMPLETED。"""
        self._require_status(
            self.status,
            TeamExecutionStatus.RUNNING,
            TeamExecutionStatus.COMPLETED.value,
        )
        self.status = TeamExecutionStatus.COMPLETED
        self.result = result
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.completed_at = utc_now()
        self.touch()

    def fail(self, error_message: str) -> None:
        """标记执行失败。RUNNING -> FAILED。"""
        self._require_status(
            self.status,
            TeamExecutionStatus.RUNNING,
            TeamExecutionStatus.FAILED.value,
        )
        self.status = TeamExecutionStatus.FAILED
        self.error_message = error_message
        self.completed_at = utc_now()
        self.touch()

    def cancel(self) -> None:
        """取消执行。PENDING|RUNNING -> CANCELLED。"""
        self._require_status(
            self.status,
            frozenset({TeamExecutionStatus.PENDING, TeamExecutionStatus.RUNNING}),
            TeamExecutionStatus.CANCELLED.value,
        )
        self.status = TeamExecutionStatus.CANCELLED
        self.completed_at = utc_now()
        self.touch()
