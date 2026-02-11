"""创建 usage_records 表。

Revision ID: h7i8j9k0l1m2
Revises: g6h7i8j9k0l1
Create Date: 2026-02-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "h7i8j9k0l1m2"
down_revision: str = "g6h7i8j9k0l1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 usage_records 表。"""
    op.create_table(
        "usage_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("model_id", sa.String(200), nullable=False),
        sa.Column("tokens_input", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_output", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recorded_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_usage_records_user_id", "usage_records", ["user_id"])
    op.create_index("idx_usage_records_agent_id", "usage_records", ["agent_id"])
    op.create_index("idx_usage_records_recorded_at", "usage_records", ["recorded_at"])
    op.create_index("idx_usage_records_model_id", "usage_records", ["model_id"])


def downgrade() -> None:
    """删除 usage_records 表。"""
    op.drop_index("idx_usage_records_model_id", table_name="usage_records")
    op.drop_index("idx_usage_records_recorded_at", table_name="usage_records")
    op.drop_index("idx_usage_records_agent_id", table_name="usage_records")
    op.drop_index("idx_usage_records_user_id", table_name="usage_records")
    op.drop_table("usage_records")
