"""PydanticRepository 基类测试 - 使用 SQLite 内存数据库。"""

import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import EntityNotFoundError
from src.shared.infrastructure.database import Base
from src.shared.infrastructure.pydantic_repository import PydanticRepository


# -- 测试用 Entity --


class FakeEntity(PydanticEntity):
    """测试实体。"""

    name: str
    status: str = "active"


# -- 测试用 ORM Model (使用项目 Base) --


class FakeModel(Base):
    """测试 ORM 模型。"""

    __tablename__ = "fakes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    status = Column(String(50), default="active")


# -- 测试用具体 Repository --


class FakeRepository(PydanticRepository[FakeEntity, FakeModel, int]):
    """测试仓库实现。"""

    entity_class = FakeEntity
    model_class = FakeModel
    _updatable_fields: frozenset[str] = frozenset({"name", "status"})


# -- Fixtures --


@pytest_asyncio.fixture
async def async_engine():
    """创建 SQLite 内存数据库引擎。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(async_engine):
    """创建异步数据库会话。"""
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as sess:
        yield sess


@pytest_asyncio.fixture
async def repo(session):
    """创建 FakeRepository 实例。"""
    return FakeRepository(session)


# -- 单元测试: 转换方法 --


@pytest.mark.unit
class TestPydanticRepositoryConversion:
    def test_to_model_converts_entity_to_orm(self):
        entity = FakeEntity(id=1, name="test", status="active")
        repo = FakeRepository.__new__(FakeRepository)
        model = repo._to_model(entity)
        assert isinstance(model, FakeModel)
        assert model.name == "test"
        assert model.status == "active"

    def test_to_model_excludes_non_column_fields(self):
        entity = FakeEntity(id=1, name="test")
        repo = FakeRepository.__new__(FakeRepository)
        model = repo._to_model(entity)
        assert not hasattr(model, "created_at")

    def test_to_entity_converts_orm_to_entity(self):
        model = FakeModel(id=1, name="test", status="active")
        repo = FakeRepository.__new__(FakeRepository)
        entity = repo._to_entity(model)
        assert isinstance(entity, FakeEntity)
        assert entity.id == 1
        assert entity.name == "test"
        assert entity.status == "active"

    def test_updatable_fields_defined(self):
        assert FakeRepository._updatable_fields == frozenset({"name", "status"})

    def test_get_update_data_filters_fields(self):
        entity = FakeEntity(id=1, name="updated", status="inactive")
        repo = FakeRepository.__new__(FakeRepository)
        data = repo._get_update_data(entity)
        assert "name" in data
        assert "status" in data
        assert "id" not in data
        assert "created_at" not in data


# -- 集成测试: SQLite 内存数据库 CRUD --


@pytest.mark.integration
class TestPydanticRepositoryCreate:
    @pytest.mark.asyncio
    async def test_create_returns_entity_with_id(self, repo):
        entity = FakeEntity(name="test-create")
        result = await repo.create(entity)
        assert result.id is not None
        assert result.name == "test-create"
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_create_persists_to_database(self, repo):
        entity = FakeEntity(name="persisted")
        created = await repo.create(entity)
        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.name == "persisted"


@pytest.mark.integration
class TestPydanticRepositoryGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_entity(self, repo):
        entity = FakeEntity(name="findable")
        created = await repo.create(entity)
        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == "findable"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_missing(self, repo):
        result = await repo.get_by_id(9999)
        assert result is None


@pytest.mark.integration
class TestPydanticRepositoryList:
    @pytest.mark.asyncio
    async def test_list_returns_all_entities(self, repo):
        await repo.create(FakeEntity(name="item-1"))
        await repo.create(FakeEntity(name="item-2"))
        await repo.create(FakeEntity(name="item-3"))
        results = await repo.list()
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_list_respects_offset_and_limit(self, repo):
        for i in range(5):
            await repo.create(FakeEntity(name=f"item-{i}"))
        results = await repo.list(offset=1, limit=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_empty_returns_empty_list(self, repo):
        results = await repo.list()
        assert results == []


@pytest.mark.integration
class TestPydanticRepositoryCount:
    @pytest.mark.asyncio
    async def test_count_returns_zero_for_empty(self, repo):
        result = await repo.count()
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_returns_correct_number(self, repo):
        await repo.create(FakeEntity(name="a"))
        await repo.create(FakeEntity(name="b"))
        result = await repo.count()
        assert result == 2


@pytest.mark.integration
class TestPydanticRepositoryUpdate:
    @pytest.mark.asyncio
    async def test_update_modifies_fields(self, repo):
        created = await repo.create(FakeEntity(name="original", status="active"))
        created.name = "modified"
        created.status = "inactive"
        updated = await repo.update(created)
        assert updated.name == "modified"
        assert updated.status == "inactive"

    @pytest.mark.asyncio
    async def test_update_persists_changes(self, repo):
        created = await repo.create(FakeEntity(name="before"))
        created.name = "after"
        await repo.update(created)
        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.name == "after"

    @pytest.mark.asyncio
    async def test_update_raises_not_found(self, repo):
        entity = FakeEntity(id=9999, name="ghost")
        with pytest.raises(EntityNotFoundError):
            await repo.update(entity)


@pytest.mark.integration
class TestPydanticRepositoryDelete:
    @pytest.mark.asyncio
    async def test_delete_removes_entity(self, repo):
        created = await repo.create(FakeEntity(name="doomed"))
        await repo.delete(created.id)
        found = await repo.get_by_id(created.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_raises_not_found(self, repo):
        with pytest.raises(EntityNotFoundError):
            await repo.delete(9999)

    @pytest.mark.asyncio
    async def test_delete_decrements_count(self, repo):
        created = await repo.create(FakeEntity(name="temp"))
        assert await repo.count() == 1
        await repo.delete(created.id)
        assert await repo.count() == 0
