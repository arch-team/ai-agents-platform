"""create_builder_sessions_table

Revision ID: u0v1w2x3y4z5
Revises: s8t9u0v1w2x3
Create Date: 2026-02-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "u0v1w2x3y4z5"
down_revision: str | Sequence[str] | None = "s8t9u0v1w2x3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 builder_sessions 表。"""
    op.create_table(
        "builder_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.String(2000), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("generated_config", sa.JSON(), nullable=True),
        sa.Column("agent_name", sa.String(200), nullable=True),
        sa.Column("created_agent_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_builder_sessions_user_id", "builder_sessions", ["user_id"])
    op.create_index("idx_builder_sessions_status", "builder_sessions", ["status"])


def downgrade() -> None:
    """删除 builder_sessions 表。"""
    op.drop_index("idx_builder_sessions_status", table_name="builder_sessions")
    op.drop_index("idx_builder_sessions_user_id", table_name="builder_sessions")
    op.drop_table("builder_sessions")
