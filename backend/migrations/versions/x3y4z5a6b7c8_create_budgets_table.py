"""create budgets table

Revision ID: x3y4z5a6b7c8
Revises: w2x3y4z5a6b7
Create Date: 2024-02-24 21:00:00.000000

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "x3y4z5a6b7c8"
down_revision: str | None = "w2x3y4z5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 budgets 表。"""
    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("budget_amount", sa.Float(), nullable=False),
        sa.Column("used_amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("alert_threshold", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("department_id", "year", "month", name="uq_department_year_month"),
        sa.CheckConstraint("year >= 2020 AND year <= 2100", name="ck_year_range"),
        sa.CheckConstraint("month >= 1 AND month <= 12", name="ck_month_range"),
        sa.CheckConstraint("budget_amount >= 0", name="ck_budget_amount_positive"),
        sa.CheckConstraint("used_amount >= 0", name="ck_used_amount_positive"),
        sa.CheckConstraint("alert_threshold >= 0 AND alert_threshold <= 1", name="ck_alert_threshold_range"),
    )
    op.create_index("ix_budgets_department_id", "budgets", ["department_id"])


def downgrade() -> None:
    """删除 budgets 表。"""
    op.drop_index("ix_budgets_department_id", table_name="budgets")
    op.drop_table("budgets")
