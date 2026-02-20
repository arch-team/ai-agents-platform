"""Eval Pipeline DTO。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TriggerPipelineDTO:
    """触发 Pipeline 的请求数据。"""

    suite_id: int
    agent_id: int
    model_ids: list[str] = field(default_factory=lambda: ["us.anthropic.claude-haiku-4-20250514-v1:0"])
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
