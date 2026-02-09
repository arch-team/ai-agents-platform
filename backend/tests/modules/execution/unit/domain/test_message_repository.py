"""IMessageRepository 接口单元测试。"""

import pytest

from src.modules.execution.domain.repositories.message_repository import (
    IMessageRepository,
)


@pytest.mark.unit
class TestIMessageRepository:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            IMessageRepository()  # type: ignore[abstract]

    def test_has_inherited_crud_methods(self) -> None:
        assert hasattr(IMessageRepository, "get_by_id")
        assert hasattr(IMessageRepository, "create")
        assert hasattr(IMessageRepository, "update")
        assert hasattr(IMessageRepository, "delete")
        assert hasattr(IMessageRepository, "list")
        assert hasattr(IMessageRepository, "count")

    def test_has_list_by_conversation_method(self) -> None:
        assert hasattr(IMessageRepository, "list_by_conversation")

    def test_has_count_by_conversation_method(self) -> None:
        assert hasattr(IMessageRepository, "count_by_conversation")
