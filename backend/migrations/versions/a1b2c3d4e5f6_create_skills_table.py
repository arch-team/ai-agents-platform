"""创建 skills 表。

Revision ID: a1b2c3d4e5f6
Revises: z5a6b7c8d9e0
Create Date: 2026-04-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str = "z5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 skills 表。"""
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("category", sa.String(50), nullable=False, server_default="general"),
        sa.Column("trigger_description", sa.String(500), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("file_path", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("creator_id", "name", name="uq_skills_creator_name"),
    )


def downgrade() -> None:
    """删除 skills 表。"""
    op.drop_table("skills")
