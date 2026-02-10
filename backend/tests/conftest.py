"""全局测试配置和 Fixture。"""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.shared.infrastructure.database import Base


# -- pytest 命令行选项 --

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--mysql",
        action="store_true",
        default=False,
        help="启用 MySQL 集成测试 (需要 MySQL 容器运行)",
    )


def pytest_configure(config: pytest.Config) -> None:
    if not config.getoption("--mysql", default=False):
        # 未启用 --mysql 时, 自动跳过 @pytest.mark.mysql 标记的测试
        config.addinivalue_line(
            "markers", "mysql: 需要 MySQL 数据库的测试",
        )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if not config.getoption("--mysql", default=False):
        skip_mysql = pytest.mark.skip(reason="需要 --mysql 选项和 MySQL 容器")
        for item in items:
            if "mysql" in item.keywords:
                item.add_marker(skip_mysql)


# -- 异步后端 --

@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """指定异步测试后端。"""
    return "asyncio"


# -- 共享数据库 Fixture --

_SQLITE_URL = "sqlite+aiosqlite:///:memory:"
_MYSQL_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "mysql+asyncmy://test:testpassword@localhost:3307/ai_agents_platform_test",
)


@pytest_asyncio.fixture
async def sqlite_engine() -> AsyncGenerator[AsyncEngine, None]:
    """SQLite 内存数据库引擎 (默认, 快速)。"""
    engine = create_async_engine(_SQLITE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def sqlite_session(sqlite_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """SQLite session (用于集成测试)。"""
    factory = async_sessionmaker(sqlite_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def mysql_engine() -> AsyncGenerator[AsyncEngine, None]:
    """MySQL 数据库引擎 (需要 MySQL 容器运行)。"""
    engine = create_async_engine(_MYSQL_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def mysql_session(mysql_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """MySQL session (用于 MySQL 集成测试)。"""
    factory = async_sessionmaker(mysql_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
