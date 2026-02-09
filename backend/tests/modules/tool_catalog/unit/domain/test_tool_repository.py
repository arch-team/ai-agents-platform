"""IToolRepository 接口单元测试。"""

import pytest

from src.modules.tool_catalog.domain.repositories.tool_repository import IToolRepository


@pytest.mark.unit
class TestIToolRepository:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            IToolRepository()  # type: ignore[abstract]

    def test_has_inherited_crud_methods(self) -> None:
        assert hasattr(IToolRepository, "get_by_id")
        assert hasattr(IToolRepository, "create")
        assert hasattr(IToolRepository, "update")
        assert hasattr(IToolRepository, "delete")
        assert hasattr(IToolRepository, "list")
        assert hasattr(IToolRepository, "count")

    def test_has_list_by_creator_method(self) -> None:
        assert hasattr(IToolRepository, "list_by_creator")

    def test_has_count_by_creator_method(self) -> None:
        assert hasattr(IToolRepository, "count_by_creator")

    def test_has_get_by_name_and_creator_method(self) -> None:
        assert hasattr(IToolRepository, "get_by_name_and_creator")

    def test_has_list_approved_method(self) -> None:
        assert hasattr(IToolRepository, "list_approved")

    def test_has_count_approved_method(self) -> None:
        assert hasattr(IToolRepository, "count_approved")

    def test_has_list_filtered_method(self) -> None:
        assert hasattr(IToolRepository, "list_filtered")

    def test_has_count_filtered_method(self) -> None:
        assert hasattr(IToolRepository, "count_filtered")
