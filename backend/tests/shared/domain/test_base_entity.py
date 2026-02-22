"""PydanticEntity 基类测试。"""

import time
from datetime import UTC, datetime

import pytest
from pydantic import ConfigDict

from src.shared.domain.base_entity import PydanticEntity


class ConcreteEntity(PydanticEntity):
    """用于测试的具体实体。"""

    model_config = ConfigDict(validate_assignment=True)

    name: str
    status: str = "draft"


@pytest.mark.unit
class TestPydanticEntityFields:
    def test_id_default_none(self):
        entity = ConcreteEntity(name="test")
        assert entity.id is None

    def test_id_can_be_set(self):
        entity = ConcreteEntity(id=42, name="test")
        assert entity.id == 42

    def test_created_at_auto_set(self):
        before = datetime.now(UTC)
        entity = ConcreteEntity(name="test")
        after = datetime.now(UTC)
        assert entity.created_at is not None
        assert before <= entity.created_at <= after

    def test_updated_at_auto_set(self):
        before = datetime.now(UTC)
        entity = ConcreteEntity(name="test")
        after = datetime.now(UTC)
        assert entity.updated_at is not None
        assert before <= entity.updated_at <= after

    def test_created_at_equals_updated_at_on_creation(self):
        entity = ConcreteEntity(name="test")
        assert entity.created_at == entity.updated_at


@pytest.mark.unit
class TestPydanticEntityTouch:
    def test_touch_updates_updated_at(self):
        entity = ConcreteEntity(name="test")
        original_updated_at = entity.updated_at
        time.sleep(0.01)
        entity.touch()
        assert entity.updated_at > original_updated_at

    def test_touch_does_not_change_created_at(self):
        entity = ConcreteEntity(name="test")
        original_created_at = entity.created_at
        time.sleep(0.01)
        entity.touch()
        assert entity.created_at == original_created_at


@pytest.mark.unit
class TestPydanticEntityValidateAssignment:
    def test_field_assignment_triggers_validation(self):
        entity = ConcreteEntity(name="test")
        entity.name = "updated"
        assert entity.name == "updated"

    def test_status_change(self):
        entity = ConcreteEntity(name="test", status="draft")
        entity.status = "active"
        assert entity.status == "active"


@pytest.mark.unit
class TestPydanticEntityEquality:
    def test_entities_with_same_id_are_equal(self):
        e1 = ConcreteEntity(id=1, name="a")
        e2 = ConcreteEntity(id=1, name="b")
        assert e1 == e2

    def test_entities_with_different_id_are_not_equal(self):
        e1 = ConcreteEntity(id=1, name="a")
        e2 = ConcreteEntity(id=2, name="a")
        assert e1 != e2

    def test_entities_without_id_are_not_equal(self):
        e1 = ConcreteEntity(name="a")
        e2 = ConcreteEntity(name="a")
        assert e1 != e2

    def test_entity_not_equal_to_different_type(self):
        e1 = ConcreteEntity(id=1, name="a")
        assert e1 != "not an entity"


@pytest.mark.unit
class TestPydanticEntityHash:
    def test_entity_with_id_is_hashable(self):
        entity = ConcreteEntity(id=1, name="test")
        assert hash(entity) == hash(1)

    def test_entities_with_same_id_have_same_hash(self):
        e1 = ConcreteEntity(id=1, name="a")
        e2 = ConcreteEntity(id=1, name="b")
        assert hash(e1) == hash(e2)

    def test_entity_can_be_used_in_set(self):
        e1 = ConcreteEntity(id=1, name="a")
        e2 = ConcreteEntity(id=1, name="b")
        e3 = ConcreteEntity(id=2, name="c")
        entity_set = {e1, e2, e3}
        assert len(entity_set) == 2
