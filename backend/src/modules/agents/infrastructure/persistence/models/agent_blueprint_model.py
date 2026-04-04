"""Agent Blueprint ORM 模型 — agent_blueprints + 关联表。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.utils import utc_now


class AgentBlueprintModel(Base):
    """Agent Blueprint ORM 模型。

    存储 Blueprint 的结构化配置 (JSON 列) 和运行时信息。
    """

    __tablename__ = "agent_blueprints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    # 结构化配置 (JSON 列)
    persona_config: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    memory_config: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    guardrails: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    model_config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    knowledge_base_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # 运行时信息
    workspace_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    runtime_arn: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    workspace_s3_uri: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class AgentBlueprintSkillModel(Base):
    """Blueprint-Skill 多对多关联表。"""

    __tablename__ = "agent_blueprint_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    blueprint_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agent_blueprints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pinned_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AgentBlueprintToolBindingModel(Base):
    """Blueprint 工具绑定表 — 带业务语义的工具引用。"""

    __tablename__ = "agent_blueprint_tool_bindings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    blueprint_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agent_blueprints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    usage_hint: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
