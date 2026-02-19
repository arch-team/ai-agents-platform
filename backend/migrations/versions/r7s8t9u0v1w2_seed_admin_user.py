"""seed_admin_user

Revision ID: r7s8t9u0v1w2
Revises: q6r7s8t9u0v1
Create Date: 2026-02-19 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "r7s8t9u0v1w2"
down_revision: Union[str, Sequence[str], None] = "q6r7s8t9u0v1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """将 admin@aiagents.dev 用户升级为 admin 角色。"""
    op.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@aiagents.dev'")


def downgrade() -> None:
    """将 admin@aiagents.dev 用户降级为 viewer 角色。"""
    op.execute("UPDATE users SET role = 'viewer' WHERE email = 'admin@aiagents.dev'")
