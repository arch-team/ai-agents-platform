"""Agent ORM 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.utils import utc_now


class AgentModel(Base):
    """Agent ORM 模型。"""

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # AgentConfig 字段展开为独立列
    model_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="anthropic.claude-3-5-sonnet-20241022-v2:0",
    )
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=2048)
    top_p: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    stop_sequences: Mapped[str] = mapped_column(Text, nullable=False, default="")
    runtime_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="agent",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_agents_owner_name"),)
