"""add_sso_fields_to_users

Revision ID: t9u0v1w2x3y4
Revises: s8t9u0v1w2x3
Create Date: 2026-02-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "v1w2x3y4z5a6"
down_revision: str | Sequence[str] | None = "u0v1w2x3y4z5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """为 users 表添加 sso_provider 和 sso_subject 列。"""
    op.add_column("users", sa.Column("sso_provider", sa.String(20), nullable=False, server_default="INTERNAL"))
    op.add_column("users", sa.Column("sso_subject", sa.String(512), nullable=True))
    op.create_index("idx_users_sso_subject", "users", ["sso_provider", "sso_subject"], unique=True)


def downgrade() -> None:
    """移除 users 表的 sso_provider 和 sso_subject 列。"""
    op.drop_index("idx_users_sso_subject", table_name="users")
    op.drop_column("users", "sso_subject")
    op.drop_column("users", "sso_provider")
