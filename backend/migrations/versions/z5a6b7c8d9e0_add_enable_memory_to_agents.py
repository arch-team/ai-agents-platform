"""为 agents 表添加 enable_memory 列。

Revision ID: z5a6b7c8d9e0
Revises: y4z5a6b7c8d9
Create Date: 2026-02-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "z5a6b7c8d9e0"
down_revision: str = "y4z5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """添加 enable_memory 列到 agents 表。Boolean 列支持 DEFAULT，单步迁移。"""
    op.add_column(
        "agents",
        sa.Column("enable_memory", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    """删除 agents 表的 enable_memory 列。"""
    op.drop_column("agents", "enable_memory")
