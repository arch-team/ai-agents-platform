"""添加 agent_blueprints + 关联表 + agents.blueprint_id。

Revision ID: b1c2d3e4f5g6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5g6"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 Blueprint 表并扩展 agents 表。"""
    # agent_blueprints 主表
    op.create_table(
        "agent_blueprints",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("persona_config", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("memory_config", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("guardrails", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("model_config_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("knowledge_base_ids", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("workspace_path", sa.String(500), nullable=False, server_default=""),
        sa.Column("runtime_arn", sa.String(500), nullable=False, server_default=""),
        sa.Column("workspace_s3_uri", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", name="uq_agent_blueprints_agent_id"),
    )
    op.create_index("ix_agent_blueprints_agent_id", "agent_blueprints", ["agent_id"])

    # agent_blueprint_skills 关联表
    op.create_table(
        "agent_blueprint_skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("blueprint_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("pinned_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["blueprint_id"], ["agent_blueprints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_blueprint_skills_blueprint_id", "agent_blueprint_skills", ["blueprint_id"])
    op.create_index("ix_agent_blueprint_skills_skill_id", "agent_blueprint_skills", ["skill_id"])

    # agent_blueprint_tool_bindings 表
    op.create_table(
        "agent_blueprint_tool_bindings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("blueprint_id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("usage_hint", sa.String(500), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["blueprint_id"], ["agent_blueprints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_blueprint_tool_bindings_blueprint_id", "agent_blueprint_tool_bindings", ["blueprint_id"])

    # agents 表添加 blueprint_id 列 (FK 引用 agent_blueprints)
    op.add_column("agents", sa.Column("blueprint_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_agents_blueprint_id", "agents", "agent_blueprints", ["blueprint_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    """回滚 Blueprint 相关表和列。"""
    op.drop_constraint("fk_agents_blueprint_id", "agents", type_="foreignkey")
    op.drop_column("agents", "blueprint_id")
    op.drop_index("ix_agent_blueprint_tool_bindings_blueprint_id", table_name="agent_blueprint_tool_bindings")
    op.drop_table("agent_blueprint_tool_bindings")
    op.drop_index("ix_agent_blueprint_skills_skill_id", table_name="agent_blueprint_skills")
    op.drop_index("ix_agent_blueprint_skills_blueprint_id", table_name="agent_blueprint_skills")
    op.drop_table("agent_blueprint_skills")
    op.drop_index("ix_agent_blueprints_agent_id", table_name="agent_blueprints")
    op.drop_table("agent_blueprints")
