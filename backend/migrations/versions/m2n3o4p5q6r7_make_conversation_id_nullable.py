"""make_conversation_id_nullable

Revision ID: m2n3o4p5q6r7
Revises: l1m2n3o4p5q6
Create Date: 2026-02-12 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "m2n3o4p5q6r7"
down_revision: str = "l1m2n3o4p5q6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """usage_records.conversation_id 改为可选，支持团队执行（无对话关联）。"""
    op.alter_column(
        "usage_records",
        "conversation_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    """恢复 conversation_id 为必填。"""
    op.alter_column(
        "usage_records",
        "conversation_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
