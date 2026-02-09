"""UserRepositoryImpl 集成测试 (SQLite 内存数据库)。"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.role import Role
from src.modules.auth.infrastructure.persistence.models.user_model import UserModel
from src.modules.auth.infrastructure.persistence.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from src.shared.infrastructure.database import Base


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def repo(session: AsyncSession) -> UserRepositoryImpl:
    return UserRepositoryImpl(session=session)


def _make_user(
    email: str = "test@example.com",
    name: str = "Test User",
    role: Role = Role.VIEWER,
) -> User:
    return User(
        email=email,
        hashed_password="hashed_password_123",
        name=name,
        role=role,
    )


@pytest.mark.integration
class TestUserRepositoryImplCreate:
    @pytest.mark.asyncio
    async def test_create_user(self, repo: UserRepositoryImpl, session: AsyncSession) -> None:
        user = _make_user()
        created = await repo.create(user)
        await session.commit()

        assert created.id is not None
        assert created.email == "test@example.com"
        assert created.name == "Test User"
        assert created.role == Role.VIEWER
        assert created.is_active is True


@pytest.mark.integration
class TestUserRepositoryImplGetById:
    @pytest.mark.asyncio
    async def test_get_by_id(self, repo: UserRepositoryImpl, session: AsyncSession) -> None:
        user = _make_user()
        created = await repo.create(user)
        await session.commit()

        found = await repo.get_by_id(created.id)  # type: ignore[arg-type]
        assert found is not None
        assert found.id == created.id
        assert found.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo: UserRepositoryImpl) -> None:
        found = await repo.get_by_id(9999)
        assert found is None


@pytest.mark.integration
class TestUserRepositoryImplGetByEmail:
    @pytest.mark.asyncio
    async def test_get_by_email(self, repo: UserRepositoryImpl, session: AsyncSession) -> None:
        user = _make_user(email="lookup@example.com")
        await repo.create(user)
        await session.commit()

        found = await repo.get_by_email("lookup@example.com")
        assert found is not None
        assert found.email == "lookup@example.com"

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, repo: UserRepositoryImpl) -> None:
        found = await repo.get_by_email("nonexistent@example.com")
        assert found is None


@pytest.mark.integration
class TestUserRepositoryImplUpdate:
    @pytest.mark.asyncio
    async def test_update_user(self, repo: UserRepositoryImpl, session: AsyncSession) -> None:
        user = _make_user()
        created = await repo.create(user)
        await session.commit()

        created.change_role(Role.ADMIN)
        updated = await repo.update(created)
        await session.commit()

        assert updated.role == Role.ADMIN
        assert updated.id == created.id


@pytest.mark.integration
class TestUserRepositoryImplDelete:
    @pytest.mark.asyncio
    async def test_delete_user(self, repo: UserRepositoryImpl, session: AsyncSession) -> None:
        user = _make_user()
        created = await repo.create(user)
        await session.commit()

        await repo.delete(created.id)  # type: ignore[arg-type]
        await session.commit()

        found = await repo.get_by_id(created.id)  # type: ignore[arg-type]
        assert found is None


@pytest.mark.integration
class TestUserRepositoryImplList:
    @pytest.mark.asyncio
    async def test_list_users(self, repo: UserRepositoryImpl, session: AsyncSession) -> None:
        await repo.create(_make_user(email="a@example.com", name="User A"))
        await repo.create(_make_user(email="b@example.com", name="User B"))
        await repo.create(_make_user(email="c@example.com", name="User C"))
        await session.commit()

        users = await repo.list(offset=0, limit=10)
        assert len(users) == 3

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(
        self, repo: UserRepositoryImpl, session: AsyncSession
    ) -> None:
        await repo.create(_make_user(email="a@example.com", name="User A"))
        await repo.create(_make_user(email="b@example.com", name="User B"))
        await repo.create(_make_user(email="c@example.com", name="User C"))
        await session.commit()

        page = await repo.list(offset=0, limit=2)
        assert len(page) == 2

    @pytest.mark.asyncio
    async def test_count_users(self, repo: UserRepositoryImpl, session: AsyncSession) -> None:
        await repo.create(_make_user(email="a@example.com", name="User A"))
        await repo.create(_make_user(email="b@example.com", name="User B"))
        await session.commit()

        count = await repo.count()
        assert count == 2
