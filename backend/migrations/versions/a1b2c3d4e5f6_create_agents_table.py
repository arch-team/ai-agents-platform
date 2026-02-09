"""create_agents_table

Revision ID: a1b2c3d4e5f6
Revises: 8d5283b682df
Create Date: 2026-02-09 17:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "8d5283b682df"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 agents 表。"""
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column(
            "model_id",
            sa.String(length=200),
            nullable=False,
            server_default="anthropic.claude-3-5-sonnet-20241022-v2:0",
        ),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2048"),
        sa.Column("top_p", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("stop_sequences", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_agents_owner_name"),
    )
    op.create_index("ix_agents_owner_id", "agents", ["owner_id"])
    op.create_index("ix_agents_status", "agents", ["status"])


def downgrade() -> None:
    """删除 agents 表。"""
    op.drop_index("ix_agents_status", table_name="agents")
    op.drop_index("ix_agents_owner_id", table_name="agents")
    op.drop_table("agents")
