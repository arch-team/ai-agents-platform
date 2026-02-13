"""add_audit_logs_append_only_triggers

Revision ID: p5q6r7s8t9u0
Revises: o4p5q6r7s8t9
Create Date: 2026-02-13 15:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "p5q6r7s8t9u0"
down_revision: str = "o4p5q6r7s8t9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """为 audit_logs 表添加 append-only 触发器，禁止 UPDATE 和 DELETE。"""
    op.execute("""
        CREATE TRIGGER audit_logs_no_update
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'audit_logs table is append-only: UPDATE not allowed'
    """)
    op.execute("""
        CREATE TRIGGER audit_logs_no_delete
        BEFORE DELETE ON audit_logs
        FOR EACH ROW
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'audit_logs table is append-only: DELETE not allowed'
    """)


def downgrade() -> None:
    """移除 audit_logs 表的 append-only 触发器。"""
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_update")
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_delete")
