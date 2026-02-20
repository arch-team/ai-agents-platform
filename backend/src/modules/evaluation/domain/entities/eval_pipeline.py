"""EvalPipeline 领域实体。"""

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus
from src.shared.domain.base_entity import PydanticEntity, utc_now


class EvalPipeline(PydanticEntity):
    """评估 Pipeline 实体，管理一次完整的评估流水线执行过程。"""

    suite_id: int
    agent_id: int
    trigger: str = Field(max_length=50)
    model_ids: list[str] = Field(min_length=1)
    status: PipelineStatus = PipelineStatus.SCHEDULED
    bedrock_job_id: str | None = None
    score_summary: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("model_ids")
    @classmethod
    def model_ids_must_not_be_empty(cls, v: list[str]) -> list[str]:
        """验证 model_ids 不能为空列表。"""
        if not v:
            msg = "model_ids 不能为空"
            raise ValueError(msg)
        return v

    def start(self) -> None:
        """启动 Pipeline。SCHEDULED -> RUNNING。"""
        self._require_status(self.status, PipelineStatus.SCHEDULED, PipelineStatus.RUNNING.value)
        self.status = PipelineStatus.RUNNING
        self.started_at = utc_now()
        self.touch()

    def complete(self, *, bedrock_job_id: str, score_summary: dict[str, Any]) -> None:
        """完成 Pipeline。RUNNING -> COMPLETED。"""
        self._require_status(self.status, PipelineStatus.RUNNING, PipelineStatus.COMPLETED.value)
        self.status = PipelineStatus.COMPLETED
        self.bedrock_job_id = bedrock_job_id
        self.score_summary = score_summary
        self.completed_at = utc_now()
        self.touch()

    def fail(self, *, error: str) -> None:
        """标记 Pipeline 失败。RUNNING -> FAILED。"""
        self._require_status(self.status, PipelineStatus.RUNNING, PipelineStatus.FAILED.value)
        self.status = PipelineStatus.FAILED
        self.error_message = error
        self.completed_at = utc_now()
        self.touch()
