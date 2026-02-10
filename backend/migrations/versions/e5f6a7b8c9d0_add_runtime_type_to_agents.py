"""add_runtime_type_to_agents

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-10 22:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 runtime_type 列到 agents 表。"""
    op.add_column(
        "agents",
        sa.Column(
            "runtime_type",
            sa.String(length=20),
            nullable=False,
            server_default="agent",
        ),
    )


def downgrade() -> None:
    """移除 agents 表的 runtime_type 列。"""
    op.drop_column("agents", "runtime_type")
