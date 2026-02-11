"""创建 templates 表。

Revision ID: i8j9k0l1m2n3
Revises: h7i8j9k0l1m2
Create Date: 2026-02-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.mysql import JSON

revision: str = "i8j9k0l1m2n3"
down_revision: str = "h7i8j9k0l1m2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 templates 表。"""
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(2000), nullable=False, server_default=""),
        sa.Column("category", sa.String(50), nullable=False, server_default="general"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("model_id", sa.String(200), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="4096"),
        sa.Column("tool_ids", JSON(), nullable=False),
        sa.Column("knowledge_base_ids", JSON(), nullable=False),
        sa.Column("tags", JSON(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_templates_name"),
    )
    op.create_index("idx_templates_creator_id", "templates", ["creator_id"])
    op.create_index("idx_templates_category", "templates", ["category"])
    op.create_index("idx_templates_status", "templates", ["status"])
    op.create_index("idx_templates_is_featured", "templates", ["is_featured"])


def downgrade() -> None:
    """删除 templates 表。"""
    op.drop_index("idx_templates_is_featured", table_name="templates")
    op.drop_index("idx_templates_status", table_name="templates")
    op.drop_index("idx_templates_category", table_name="templates")
    op.drop_index("idx_templates_creator_id", table_name="templates")
    op.drop_table("templates")
