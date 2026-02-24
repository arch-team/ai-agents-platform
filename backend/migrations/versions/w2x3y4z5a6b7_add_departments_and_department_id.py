"""add_departments_and_department_id

Revision ID: w2x3y4z5a6b7
Revises: v1w2x3y4z5a6
Create Date: 2026-02-24 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "w2x3y4z5a6b7"
down_revision: str | Sequence[str] | None = "v1w2x3y4z5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. 创建 departments 表
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_departments_code", "departments", ["code"])

    # 2. 为所有业务表添加 department_id 列 (允许 NULL, 渐进填充)
    tables = [
        "users",
        "agents",
        "tools",
        "knowledge_bases",
        "conversations",
        "team_executions",
        "builder_sessions",
    ]
    for table in tables:
        op.add_column(table, sa.Column("department_id", sa.Integer(), nullable=True))
        op.create_index(f"ix_{table}_department_id", table, ["department_id"])


def downgrade() -> None:
    tables = [
        "builder_sessions",
        "team_executions",
        "conversations",
        "knowledge_bases",
        "tools",
        "agents",
        "users",
    ]
    for table in tables:
        op.drop_index(f"ix_{table}_department_id", table_name=table)
        op.drop_column(table, "department_id")

    op.drop_index("ix_departments_code", table_name="departments")
    op.drop_table("departments")
