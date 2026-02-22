"""BuilderSession ORM 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.utils import utc_now


class BuilderSessionModel(Base):
    """Builder 会话 ORM 模型。"""

    __tablename__ = "builder_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(String(2000), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    generated_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # type: ignore[type-arg]
    agent_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_agent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("agents.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        Index("idx_builder_sessions_user_id", "user_id"),
        Index("idx_builder_sessions_status", "status"),
    )
