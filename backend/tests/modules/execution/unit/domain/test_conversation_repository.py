"""IConversationRepository 接口单元测试。"""

import pytest

from src.modules.execution.domain.repositories.conversation_repository import (
    IConversationRepository,
)


@pytest.mark.unit
class TestIConversationRepository:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            IConversationRepository()  # type: ignore[abstract]

    def test_has_inherited_crud_methods(self) -> None:
        assert hasattr(IConversationRepository, "get_by_id")
        assert hasattr(IConversationRepository, "create")
        assert hasattr(IConversationRepository, "update")
        assert hasattr(IConversationRepository, "delete")
        assert hasattr(IConversationRepository, "list")
        assert hasattr(IConversationRepository, "count")

    def test_has_list_by_user_method(self) -> None:
        assert hasattr(IConversationRepository, "list_by_user")

    def test_has_count_by_user_method(self) -> None:
        assert hasattr(IConversationRepository, "count_by_user")
