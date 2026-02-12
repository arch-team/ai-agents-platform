"""为 agents 表添加 enable_teams 列。

Revision ID: k0l1m2n3o4p5
Revises: j9k0l1m2n3o4
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "k0l1m2n3o4p5"
down_revision: str = "j9k0l1m2n3o4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """添加 enable_teams 列到 agents 表。"""
    op.add_column(
        "agents",
        sa.Column("enable_teams", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """删除 agents 表的 enable_teams 列。"""
    op.drop_column("agents", "enable_teams")
