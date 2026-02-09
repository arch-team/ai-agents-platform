"""IRepository 泛型接口测试。"""

import pytest
from abc import ABC

from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.repositories import IRepository


@pytest.mark.unit
class TestIRepositoryInterface:
    def test_is_abstract_class(self):
        assert issubclass(IRepository, ABC)

    def test_cannot_instantiate_directly(self):
        """IRepository 是抽象类，不能直接实例化。"""
        with pytest.raises(TypeError):
            IRepository()  # type: ignore[abstract]

    def test_has_get_by_id_method(self):
        assert hasattr(IRepository, "get_by_id")

    def test_has_list_method(self):
        assert hasattr(IRepository, "list")

    def test_has_count_method(self):
        assert hasattr(IRepository, "count")

    def test_has_create_method(self):
        assert hasattr(IRepository, "create")

    def test_has_update_method(self):
        assert hasattr(IRepository, "update")

    def test_has_delete_method(self):
        assert hasattr(IRepository, "delete")


class DummyEntity(PydanticEntity):
    """用于测试的实体。"""

    name: str


class ConcreteRepository(IRepository[DummyEntity, int]):
    """用于测试的具体仓库实现。"""

    async def get_by_id(self, entity_id: int) -> DummyEntity | None:
        return None

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[DummyEntity]:
        return []

    async def count(self) -> int:
        return 0

    async def create(self, entity: DummyEntity) -> DummyEntity:
        return entity

    async def update(self, entity: DummyEntity) -> DummyEntity:
        return entity

    async def delete(self, entity_id: int) -> None:
        return


@pytest.mark.unit
class TestConcreteRepository:
    """验证具体实现可以正确继承 IRepository。"""

    def test_concrete_repo_is_subclass(self):
        assert issubclass(ConcreteRepository, IRepository)

    def test_concrete_repo_can_instantiate(self):
        repo = ConcreteRepository()
        assert repo is not None
