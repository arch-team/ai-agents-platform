"""IMessageRepository 接口单元测试。"""

import pytest

from src.modules.execution.domain.repositories.message_repository import (
    IMessageRepository,
)


_CRUD_METHODS = ["get_by_id", "create", "update", "delete", "list", "count"]
_CUSTOM_METHODS = ["list_by_conversation", "count_by_conversation"]


@pytest.mark.unit
class TestIMessageRepository:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            IMessageRepository()  # type: ignore[abstract]

    @pytest.mark.parametrize("method", _CRUD_METHODS + _CUSTOM_METHODS)
    def test_has_required_method(self, method: str) -> None:
        assert hasattr(IMessageRepository, method)
