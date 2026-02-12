"""create_evaluation_tables

Revision ID: n3o4p5q6r7s8
Revises: m2n3o4p5q6r7
Create Date: 2026-02-12 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "n3o4p5q6r7s8"
down_revision: str = "m2n3o4p5q6r7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建评估模块所需的 4 张表。"""
    # test_suites
    op.create_table(
        "test_suites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_test_suites_agent_id", "test_suites", ["agent_id"])
    op.create_index("idx_test_suites_owner_id", "test_suites", ["owner_id"])
    op.create_index("idx_test_suites_status", "test_suites", ["status"])

    # test_cases
    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("suite_id", sa.Integer(), nullable=False),
        sa.Column("input_prompt", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("evaluation_criteria", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["suite_id"], ["test_suites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_test_cases_suite_id", "test_cases", ["suite_id"])

    # evaluation_runs
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("suite_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["suite_id"], ["test_suites.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_evaluation_runs_suite_id", "evaluation_runs", ["suite_id"])
    op.create_index("idx_evaluation_runs_user_id", "evaluation_runs", ["user_id"])
    op.create_index("idx_evaluation_runs_status", "evaluation_runs", ["status"])

    # evaluation_results
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("actual_output", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["evaluation_runs.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["test_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_evaluation_results_run_id", "evaluation_results", ["run_id"])
    op.create_index("idx_evaluation_results_case_id", "evaluation_results", ["case_id"])


def downgrade() -> None:
    """删除评估模块所有表。"""
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_runs")
    op.drop_table("test_cases")
    op.drop_table("test_suites")
