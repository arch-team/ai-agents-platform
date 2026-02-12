"""创建 team_executions 和 team_execution_logs 表。

Revision ID: l1m2n3o4p5q6
Revises: k0l1m2n3o4p5
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "l1m2n3o4p5q6"
down_revision: str = "k0l1m2n3o4p5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 team_executions 和 team_execution_logs 表。"""
    op.create_table(
        "team_executions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_team_executions_agent_id", "team_executions", ["agent_id"])
    op.create_index("ix_team_executions_user_id", "team_executions", ["user_id"])
    op.create_index("ix_team_executions_status", "team_executions", ["status"])

    op.create_table(
        "team_execution_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("execution_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("log_type", sa.String(length=20), nullable=False, server_default="progress"),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["team_executions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_team_execution_logs_execution_id", "team_execution_logs", ["execution_id"])


def downgrade() -> None:
    """删除 team_execution_logs 和 team_executions 表。"""
    op.drop_index("ix_team_execution_logs_execution_id", table_name="team_execution_logs")
    op.drop_table("team_execution_logs")
    op.drop_index("ix_team_executions_status", table_name="team_executions")
    op.drop_index("ix_team_executions_user_id", table_name="team_executions")
    op.drop_index("ix_team_executions_agent_id", table_name="team_executions")
    op.drop_table("team_executions")
