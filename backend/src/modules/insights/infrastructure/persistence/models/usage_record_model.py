"""UsageRecord ORM 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.utils import utc_now


class UsageRecordModel(Base):
    """UsageRecord ORM 模型。"""

    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agents.id"),
        nullable=False,
    )
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False,
    )
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    tokens_input: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        Index("idx_usage_records_user_id", "user_id"),
        Index("idx_usage_records_agent_id", "agent_id"),
        Index("idx_usage_records_recorded_at", "recorded_at"),
        Index("idx_usage_records_model_id", "model_id"),
    )
