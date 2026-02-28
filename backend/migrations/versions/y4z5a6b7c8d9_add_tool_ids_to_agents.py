"""为 agents 表添加 tool_ids 列。

Revision ID: y4z5a6b7c8d9
Revises: x3y4z5a6b7c8
Create Date: 2026-02-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "y4z5a6b7c8d9"
down_revision: str = "x3y4z5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """添加 tool_ids 列到 agents 表。"""
    op.add_column(
        "agents",
        sa.Column("tool_ids", sa.Text(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    """删除 agents 表的 tool_ids 列。"""
    op.drop_column("agents", "tool_ids")
