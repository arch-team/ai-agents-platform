"""EvalPipeline ORM 模型。"""

import json
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.utils import utc_now


class EvalPipelineModel(Base):
    """评估流水线 ORM 模型。"""

    __tablename__ = "eval_pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    suite_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("test_suites.id"),
        nullable=False,
    )
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agents.id"),
        nullable=False,
    )
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    model_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    bedrock_job_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    score_summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        Index("idx_eval_pipelines_suite_id", "suite_id"),
        Index("idx_eval_pipelines_agent_id", "agent_id"),
        Index("idx_eval_pipelines_status", "status"),
    )

    @property
    def model_ids(self) -> list[str]:
        """反序列化 model_ids_json 为 list[str]。"""
        return json.loads(self.model_ids_json)  # type: ignore[no-any-return]

    @property
    def score_summary(self) -> dict[str, object]:
        """反序列化 score_summary_json 为 dict。"""
        return json.loads(self.score_summary_json)  # type: ignore[no-any-return]
