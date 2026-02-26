#!/usr/bin/env python
"""数据库迁移并发锁 -- 使用 MySQL Advisory Lock 确保多 ECS Task 串行执行 Alembic 迁移。

安全特性:
- Advisory Lock 与连接绑定，容器崩溃时连接断开锁自动释放
- 锁获取超时 120s，超时后仍执行迁移（避免锁成为单点故障）
- 迁移失败时进程退出码非零，ECS 健康检查会重启容器
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from urllib.parse import urlparse

import asyncmy


# 锁名称和超时时间（秒）
LOCK_NAME = "alembic_migration"
LOCK_TIMEOUT = 120


def _parse_database_url() -> dict[str, str | int]:
    """从 DATABASE_URL 环境变量解析 MySQL 连接参数。"""
    url = os.environ.get("DATABASE_URL", "")
    # 替换 SQLAlchemy 方言前缀，使 urlparse 正确解析
    parsed = urlparse(url.replace("mysql+asyncmy://", "mysql://"))
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": parsed.username or "root",
        "password": parsed.password or "",
        "db": parsed.path.lstrip("/"),
    }


def _run_alembic() -> int:
    """执行 alembic upgrade head，返回进程退出码。"""
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        check=False,
    )
    return result.returncode


async def _migrate_with_lock() -> int:
    """获取 Advisory Lock 后执行迁移，返回退出码。"""
    conn_params = _parse_database_url()
    conn: asyncmy.Connection | None = None
    lock_acquired = False

    try:
        conn = await asyncmy.connect(
            host=conn_params["host"],
            port=int(conn_params["port"]),
            user=str(conn_params["user"]),
            password=str(conn_params["password"]),
            db=str(conn_params["db"]),
        )
        print(f"[migrate] MySQL 连接成功: {conn_params['host']}:{conn_params['port']}")

        # 尝试获取 Advisory Lock
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT GET_LOCK(%s, %s)", (LOCK_NAME, LOCK_TIMEOUT))
            row = await cursor.fetchone()
            lock_acquired = row is not None and row[0] == 1

        if lock_acquired:
            print(f"[migrate] 获取 Advisory Lock '{LOCK_NAME}' 成功，开始执行迁移...")
        else:
            print(
                f"[migrate] 警告: 获取 Advisory Lock '{LOCK_NAME}' 超时 ({LOCK_TIMEOUT}s)，"
                "仍尝试执行迁移（避免锁成为阻塞点）",
            )

        # 执行 Alembic 迁移
        exit_code = _run_alembic()

        if exit_code == 0:
            print("[migrate] 迁移完成")
        else:
            print(f"[migrate] 迁移失败，退出码: {exit_code}")

        return exit_code

    except Exception as exc:
        # 连接失败时降级为直接执行迁移（容错设计）
        print(f"[migrate] MySQL 连接/锁操作异常: {exc}，降级为直接执行迁移")
        return _run_alembic()

    finally:
        # 无论成功/失败，释放锁并关闭连接
        if conn is not None:
            try:
                if lock_acquired:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME,))
                    print(f"[migrate] Advisory Lock '{LOCK_NAME}' 已释放")
                conn.close()
            except Exception as release_exc:
                print(f"[migrate] 释放锁/关闭连接异常（不影响迁移结果）: {release_exc}")


def main() -> None:
    """入口函数。"""
    exit_code = asyncio.run(_migrate_with_lock())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
