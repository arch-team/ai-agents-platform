"""为 agents 表添加 tool_ids 列。

Revision ID: y4z5a6b7c8d9
Revises: x3y4z5a6b7c8
Create Date: 2026-02-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "y4z5a6b7c8d9"
down_revision: str = "x3y4z5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """添加 tool_ids 列到 agents 表。

    数据迁移策略:
    - MySQL TEXT 列不支持 DEFAULT，分三步迁移: 添加可空列 → 填充默认值 → 设为 NOT NULL
    - 历史 Agent: 默认空列表 '[]', 用户通过 API 手动绑定工具
    - 新 Agent: 创建时由业务层填充 tool_ids
    """
    # Step 1: 添加可空 TEXT 列
    op.add_column(
        "agents",
        sa.Column("tool_ids", sa.Text(), nullable=True),
    )
    # Step 2: 填充现有记录默认值
    op.execute("UPDATE agents SET tool_ids = '[]' WHERE tool_ids IS NULL")
    # Step 3: 设为 NOT NULL
    op.alter_column("agents", "tool_ids", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    """删除 agents 表的 tool_ids 列。"""
    op.drop_column("agents", "tool_ids")
