"""Agent ORM 模型。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.constants import (
    AGENT_DEFAULT_ENABLE_TEAMS,
    AGENT_DEFAULT_MAX_TOKENS,
    AGENT_DEFAULT_MODEL_ID,
    AGENT_DEFAULT_RUNTIME_TYPE,
    AGENT_DEFAULT_TEMPERATURE,
    AGENT_DEFAULT_TOP_P,
)
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
        default=AGENT_DEFAULT_MODEL_ID,
    )
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=AGENT_DEFAULT_TEMPERATURE)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=AGENT_DEFAULT_MAX_TOKENS)
    top_p: Mapped[float] = mapped_column(Float, nullable=False, default=AGENT_DEFAULT_TOP_P)
    stop_sequences: Mapped[str] = mapped_column(Text, nullable=False, default="")
    runtime_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AGENT_DEFAULT_RUNTIME_TYPE,
    )
    enable_teams: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=AGENT_DEFAULT_ENABLE_TEAMS,
    )
    enable_memory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # JSON 序列化的 list[int], 存储绑定的 Tool ID 列表
    tool_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    department_id: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None, index=True)
    blueprint_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("agent_blueprints.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_agents_owner_name"),)
