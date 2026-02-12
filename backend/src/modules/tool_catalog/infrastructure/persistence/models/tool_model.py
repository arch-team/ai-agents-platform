"""Tool ORM 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.utils import utc_now


class ToolModel(Base):
    """Tool ORM 模型。"""

    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    tool_type: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    creator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # ToolConfig 展开为独立列
    server_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    transport: Mapped[str] = mapped_column(String(30), nullable=False, default="stdio")
    endpoint_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    method: Mapped[str] = mapped_column(String(10), nullable=False, default="POST")
    headers: Mapped[str] = mapped_column(Text, nullable=False, default="")
    runtime: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    handler: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    code_uri: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    auth_type: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    auth_config: Mapped[str] = mapped_column(Text, nullable=False, default="")
    allowed_roles: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default='["admin","developer"]',
    )

    # Gateway 同步字段
    gateway_target_id: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    # 审批字段
    reviewer_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )
    review_comment: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        UniqueConstraint("creator_id", "name", name="uq_tools_creator_name"),
        Index("ix_tools_status_type", "status", "tool_type"),
    )
