"""数据库会话管理。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


_NOT_INITIALIZED_MSG = "Database not initialized. Call init_db() first."


class Base(DeclarativeBase):
    """SQLAlchemy ORM 声明基类。"""


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str, *, echo: bool = False) -> None:
    """初始化数据库引擎和会话工厂。"""
    global _engine, _session_factory  # noqa: PLW0603
    _engine = create_async_engine(database_url, echo=echo, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine() -> AsyncEngine:
    """获取当前数据库引擎。"""
    if _engine is None:
        raise RuntimeError(_NOT_INITIALIZED_MSG)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取 session factory（用于流式等需要独立管理 session 生命周期的场景）。"""
    if _session_factory is None:
        raise RuntimeError(_NOT_INITIALIZED_MSG)
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入: 获取异步数据库会话。"""
    if _session_factory is None:
        raise RuntimeError(_NOT_INITIALIZED_MSG)
    async with _session_factory() as session:
        yield session


async def create_all_tables() -> None:
    """创建所有表（开发/测试用）。"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
