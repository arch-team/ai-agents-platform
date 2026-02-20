"""add_eval_pipelines_table

Revision ID: s8t9u0v1w2x3
Revises: r7s8t9u0v1w2
Create Date: 2026-02-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "s8t9u0v1w2x3"
down_revision: str | Sequence[str] | None = "r7s8t9u0v1w2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 eval_pipelines 表。"""
    op.create_table(
        "eval_pipelines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("suite_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("trigger", sa.String(50), nullable=False),
        sa.Column("model_ids_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("bedrock_job_id", sa.String(200), nullable=True),
        sa.Column("score_summary_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["suite_id"], ["test_suites.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_eval_pipelines_suite_id", "eval_pipelines", ["suite_id"])
    op.create_index("idx_eval_pipelines_agent_id", "eval_pipelines", ["agent_id"])
    op.create_index("idx_eval_pipelines_status", "eval_pipelines", ["status"])


def downgrade() -> None:
    """删除 eval_pipelines 表。"""
    op.drop_index("idx_eval_pipelines_status", table_name="eval_pipelines")
    op.drop_index("idx_eval_pipelines_agent_id", table_name="eval_pipelines")
    op.drop_index("idx_eval_pipelines_suite_id", table_name="eval_pipelines")
    op.drop_table("eval_pipelines")
