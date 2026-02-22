"""UserRepositoryImpl 集成测试。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.role import Role
from src.modules.auth.infrastructure.persistence.repositories.user_repository_impl import (
    UserRepositoryImpl,
)


# 使用全局 conftest.py 中的 sqlite_session fixture
@pytest.fixture
def session(sqlite_session: AsyncSession) -> AsyncSession:
    return sqlite_session


@pytest.fixture
def repo(session: AsyncSession) -> UserRepositoryImpl:
    return UserRepositoryImpl(session=session)


# MySQL 版本的 fixture
@pytest.fixture
def mysql_repo(mysql_session: AsyncSession) -> UserRepositoryImpl:
    return UserRepositoryImpl(session=mysql_session)


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
        self, repo: UserRepositoryImpl, session: AsyncSession,
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


# ── MySQL 集成测试 (需要 --mysql 选项) ──


@pytest.mark.mysql
@pytest.mark.integration
class TestUserRepositoryMySQLCrud:
    """UserRepositoryImpl MySQL 集成测试: 验证真实 MySQL 方言兼容性。"""

    @pytest.mark.asyncio
    async def test_create_and_get(self, mysql_repo: UserRepositoryImpl, mysql_session: AsyncSession) -> None:
        user = _make_user(email="mysql@example.com")
        created = await mysql_repo.create(user)
        await mysql_session.commit()

        assert created.id is not None
        found = await mysql_repo.get_by_id(created.id)
        assert found is not None
        assert found.email == "mysql@example.com"

    @pytest.mark.asyncio
    async def test_update(self, mysql_repo: UserRepositoryImpl, mysql_session: AsyncSession) -> None:
        user = _make_user(email="update-mysql@example.com")
        created = await mysql_repo.create(user)
        await mysql_session.commit()

        created.change_role(Role.ADMIN)
        updated = await mysql_repo.update(created)
        await mysql_session.commit()

        assert updated.role == Role.ADMIN

    @pytest.mark.asyncio
    async def test_delete(self, mysql_repo: UserRepositoryImpl, mysql_session: AsyncSession) -> None:
        user = _make_user(email="delete-mysql@example.com")
        created = await mysql_repo.create(user)
        await mysql_session.commit()

        await mysql_repo.delete(created.id)
        await mysql_session.commit()

        found = await mysql_repo.get_by_id(created.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_list_and_count(self, mysql_repo: UserRepositoryImpl, mysql_session: AsyncSession) -> None:
        await mysql_repo.create(_make_user(email="m1@example.com", name="MySQL User 1"))
        await mysql_repo.create(_make_user(email="m2@example.com", name="MySQL User 2"))
        await mysql_session.commit()

        users = await mysql_repo.list(offset=0, limit=10)
        assert len(users) == 2

        count = await mysql_repo.count()
        assert count == 2
