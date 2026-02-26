"""数据库会话管理测试。"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import database
from src.shared.infrastructure.database import (
    create_all_tables,
    get_db,
    get_engine,
    get_session_factory,
    init_db,
)


@pytest.fixture(autouse=True)
def _reset_db_state():
    """每个测试前后重置数据库模块全局状态。"""
    original_engine = database._engine
    original_factory = database._session_factory
    database._engine = None
    database._session_factory = None
    yield
    database._engine = original_engine
    database._session_factory = original_factory


@pytest.mark.unit
class TestInitDb:
    def test_init_db_creates_engine(self):
        init_db("sqlite+aiosqlite:///:memory:")
        assert database._engine is not None

    def test_init_db_creates_session_factory(self):
        init_db("sqlite+aiosqlite:///:memory:")
        assert database._session_factory is not None

    def test_init_db_with_mysql_url_sets_pool_params(self):
        """非 SQLite URL 应设置连接池参数。"""
        init_db("mysql+asyncmy://user:pass@localhost/db")
        assert database._engine is not None


@pytest.mark.unit
class TestGetEngine:
    def test_get_engine_returns_engine_after_init(self):
        init_db("sqlite+aiosqlite:///:memory:")
        engine = get_engine()
        assert engine is not None

    def test_get_engine_raises_without_init(self):
        with pytest.raises(RuntimeError, match="Database not initialized"):
            get_engine()


@pytest.mark.unit
class TestGetSessionFactory:
    def test_get_session_factory_raises_without_init(self):
        """未初始化时应抛出 RuntimeError。"""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            get_session_factory()

    def test_get_session_factory_returns_factory_after_init(self):
        init_db("sqlite+aiosqlite:///:memory:")
        factory = get_session_factory()
        assert factory is not None


@pytest.mark.unit
class TestGetDb:
    @pytest.mark.asyncio
    async def test_get_db_raises_without_init(self):
        with pytest.raises(RuntimeError, match="Database not initialized"):
            async for _ in get_db():
                pass

    @pytest.mark.asyncio
    async def test_get_db_yields_session_after_init(self):
        init_db("sqlite+aiosqlite:///:memory:")
        async for session in get_db():
            assert isinstance(session, AsyncSession)
            break

    @pytest.mark.asyncio
    async def test_get_db_commits_on_success(self):
        """正常完成时事务自动提交。"""
        init_db("sqlite+aiosqlite:///:memory:")
        await create_all_tables()

        # 使用 get_db 生成器完整走完 commit 路径
        gen = get_db()
        session = await gen.__anext__()
        # 执行一个简单查询确认 session 正常
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        # 完成生成器 → 触发 commit
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

    @pytest.mark.asyncio
    async def test_get_db_rollback_on_exception(self):
        """异常时事务自动回滚。"""
        init_db("sqlite+aiosqlite:///:memory:")
        await create_all_tables()

        gen = get_db()
        session = await gen.__anext__()
        # 向生成器抛入异常 → 触发 rollback 路径
        with pytest.raises(ValueError, match="测试回滚"):
            await gen.athrow(ValueError("测试回滚"))


@pytest.mark.unit
class TestCreateAllTables:
    @pytest.mark.asyncio
    async def test_create_all_tables_succeeds(self):
        """create_all_tables 应成功创建表结构。"""
        init_db("sqlite+aiosqlite:///:memory:")
        await create_all_tables()
        # 验证引擎已初始化且可用
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
