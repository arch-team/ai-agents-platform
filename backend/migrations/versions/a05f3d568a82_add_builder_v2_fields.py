"""为 builder_sessions 表添加 V2 字段 (多轮对话 + Blueprint)。

Revision ID: a05f3d568a82
Revises: 020f072419b6
Create Date: 2026-04-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a05f3d568a82"
down_revision: str | Sequence[str] | None = "020f072419b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """添加 V2 多轮对话和 Blueprint 字段。"""
    op.add_column("builder_sessions", sa.Column("messages", sa.JSON(), nullable=True))
    op.add_column("builder_sessions", sa.Column("template_id", sa.Integer(), nullable=True))
    op.add_column("builder_sessions", sa.Column("selected_skill_ids", sa.JSON(), nullable=True))
    op.add_column("builder_sessions", sa.Column("generated_blueprint", sa.JSON(), nullable=True))


def downgrade() -> None:
    """移除 V2 字段。"""
    op.drop_column("builder_sessions", "generated_blueprint")
    op.drop_column("builder_sessions", "selected_skill_ids")
    op.drop_column("builder_sessions", "template_id")
    op.drop_column("builder_sessions", "messages")
