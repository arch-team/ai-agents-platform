"""Eval Pipeline DTO。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45


@dataclass
class TriggerPipelineDTO:
    """触发 Pipeline 的请求数据。"""

    suite_id: int
    agent_id: int
    model_ids: list[str] = field(default_factory=lambda: [MODEL_CLAUDE_HAIKU_45])
    trigger: str = "manual"


@dataclass
class EvalPipelineDTO:
    """Eval Pipeline 响应数据。"""

    id: int
    suite_id: int
    agent_id: int
    trigger: str
    model_ids: list[str]
    status: str
    bedrock_job_id: str | None
    score_summary: dict[str, Any]
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
