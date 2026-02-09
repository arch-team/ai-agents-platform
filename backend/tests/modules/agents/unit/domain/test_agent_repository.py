"""IAgentRepository 接口单元测试。"""

import pytest

from src.modules.agents.domain.repositories.agent_repository import IAgentRepository


@pytest.mark.unit
class TestIAgentRepository:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            IAgentRepository()  # type: ignore[abstract]

    def test_has_inherited_crud_methods(self) -> None:
        assert hasattr(IAgentRepository, "get_by_id")
        assert hasattr(IAgentRepository, "create")
        assert hasattr(IAgentRepository, "update")
        assert hasattr(IAgentRepository, "delete")
        assert hasattr(IAgentRepository, "list")
        assert hasattr(IAgentRepository, "count")

    def test_has_list_by_owner_method(self) -> None:
        assert hasattr(IAgentRepository, "list_by_owner")

    def test_has_count_by_owner_method(self) -> None:
        assert hasattr(IAgentRepository, "count_by_owner")

    def test_has_get_by_name_and_owner_method(self) -> None:
        assert hasattr(IAgentRepository, "get_by_name_and_owner")

    def test_has_list_by_owner_and_status_method(self) -> None:
        assert hasattr(IAgentRepository, "list_by_owner_and_status")

    def test_has_count_by_owner_and_status_method(self) -> None:
        assert hasattr(IAgentRepository, "count_by_owner_and_status")
