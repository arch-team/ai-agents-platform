"""create_tools_table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-10 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 tools 表。"""
    op.create_table(
        "tools",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("tool_type", sa.String(length=20), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="1.0.0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("server_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("transport", sa.String(length=30), nullable=False, server_default="stdio"),
        sa.Column("endpoint_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("method", sa.String(length=10), nullable=False, server_default="POST"),
        sa.Column("headers", sa.Text(), nullable=False, server_default=""),
        sa.Column("runtime", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("handler", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("code_uri", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("auth_type", sa.String(length=20), nullable=False, server_default="none"),
        sa.Column("auth_config", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "allowed_roles",
            sa.Text(),
            nullable=False,
            server_default='["admin","developer"]',
        ),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column(
            "review_comment", sa.String(length=1000), nullable=False, server_default=""
        ),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("creator_id", "name", name="uq_tools_creator_name"),
    )
    op.create_index("ix_tools_creator_id", "tools", ["creator_id"])
    op.create_index("ix_tools_status", "tools", ["status"])
    op.create_index("ix_tools_status_type", "tools", ["status", "tool_type"])


def downgrade() -> None:
    """删除 tools 表。"""
    op.drop_index("ix_tools_status_type", table_name="tools")
    op.drop_index("ix_tools_status", table_name="tools")
    op.drop_index("ix_tools_creator_id", table_name="tools")
    op.drop_table("tools")
