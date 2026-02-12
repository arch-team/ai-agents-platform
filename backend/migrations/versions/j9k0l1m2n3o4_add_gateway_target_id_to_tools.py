"""为 tools 表添加 gateway_target_id 列。

Revision ID: j9k0l1m2n3o4
Revises: i8j9k0l1m2n3
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "j9k0l1m2n3o4"
down_revision: str = "i8j9k0l1m2n3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """添加 gateway_target_id 列到 tools 表。"""
    op.add_column(
        "tools",
        sa.Column("gateway_target_id", sa.String(200), nullable=False, server_default=""),
    )


def downgrade() -> None:
    """删除 tools 表的 gateway_target_id 列。"""
    op.drop_column("tools", "gateway_target_id")
