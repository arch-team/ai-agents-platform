"""add_error_message_to_knowledge_bases

Revision ID: q6r7s8t9u0v1
Revises: p5q6r7s8t9u0
Create Date: 2026-02-18 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "q6r7s8t9u0v1"
down_revision: Union[str, Sequence[str], None] = "p5q6r7s8t9u0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """为 knowledge_bases 表添加缺失的 error_message 列。"""
    op.add_column(
        "knowledge_bases",
        sa.Column("error_message", sa.String(length=2000), nullable=False, server_default=""),
    )


def downgrade() -> None:
    """移除 knowledge_bases 表的 error_message 列。"""
    op.drop_column("knowledge_bases", "error_message")
