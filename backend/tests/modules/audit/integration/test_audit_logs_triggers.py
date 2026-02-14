"""audit_logs 表 append-only 触发器集成测试。

这些测试验证数据库层的 append-only 约束（MySQL 触发器）。
由于 SQLite 不支持 SIGNAL 语法，测试标记为 mysql，
仅在 --mysql 选项启用时运行。
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database import get_session_factory


@pytest.fixture
async def db_session():  # type: ignore[misc]
    """获取异步数据库会话。"""
    factory = get_session_factory()
    async with factory() as session:
        yield session
        await session.rollback()


async def _insert_audit_log(session: AsyncSession) -> int:
    """插入一条测试审计日志并返回其 ID。"""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    result = await session.execute(
        text("""
            INSERT INTO audit_logs
                (actor_id, actor_name, action, category, resource_type,
                 resource_id, module, result, occurred_at, created_at, updated_at)
            VALUES
                (:actor_id, :actor_name, :action, :category, :resource_type,
                 :resource_id, :module, :result, :occurred_at, :created_at, :updated_at)
        """),
        {
            "actor_id": 1,
            "actor_name": "测试用户",
            "action": "create",
            "category": "agent_management",
            "resource_type": "agent",
            "resource_id": "test-1",
            "module": "agents",
            "result": "success",
            "occurred_at": now,
            "created_at": now,
            "updated_at": now,
        },
    )
    await session.flush()
    return result.lastrowid  # type: ignore[return-value]


@pytest.mark.mysql
@pytest.mark.integration
@pytest.mark.asyncio
class TestAuditLogsAppendOnlyTriggers:
    """验证 audit_logs 表的 append-only 数据库触发器。"""

    async def test_insert_succeeds(self, db_session: AsyncSession) -> None:
        """INSERT 操作应正常执行。"""
        row_id = await _insert_audit_log(db_session)
        assert row_id is not None
        assert row_id > 0

    async def test_update_blocked_by_trigger(self, db_session: AsyncSession) -> None:
        """UPDATE 操作应被触发器拒绝。"""
        row_id = await _insert_audit_log(db_session)

        with pytest.raises(Exception, match="append-only.*UPDATE not allowed"):
            await db_session.execute(
                text("UPDATE audit_logs SET actor_name = :name WHERE id = :id"),
                {"name": "篡改者", "id": row_id},
            )

    async def test_delete_blocked_by_trigger(self, db_session: AsyncSession) -> None:
        """DELETE 操作应被触发器拒绝。"""
        row_id = await _insert_audit_log(db_session)

        with pytest.raises(Exception, match="append-only.*DELETE not allowed"):
            await db_session.execute(
                text("DELETE FROM audit_logs WHERE id = :id"),
                {"id": row_id},
            )
