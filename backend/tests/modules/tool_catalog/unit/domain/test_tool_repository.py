"""IToolRepository 接口单元测试。"""

import pytest

from src.modules.tool_catalog.domain.repositories.tool_repository import IToolRepository


_CRUD_METHODS = ["get_by_id", "create", "update", "delete", "list", "count"]
_CUSTOM_METHODS = [
    "list_by_creator",
    "count_by_creator",
    "get_by_name_and_creator",
    "list_approved",
    "count_approved",
    "list_filtered",
    "count_filtered",
]


@pytest.mark.unit
class TestIToolRepository:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            IToolRepository()  # type: ignore[abstract]

    @pytest.mark.parametrize("method", _CRUD_METHODS + _CUSTOM_METHODS)
    def test_has_required_method(self, method: str) -> None:
        assert hasattr(IToolRepository, method)
