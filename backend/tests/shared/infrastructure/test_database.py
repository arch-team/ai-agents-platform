"""数据库会话管理测试。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import database
from src.shared.infrastructure.database import get_db, get_engine, init_db


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
