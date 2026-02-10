"""IAgentRepository 接口单元测试。"""

import pytest

from src.modules.agents.domain.repositories.agent_repository import IAgentRepository


_CRUD_METHODS = ["get_by_id", "create", "update", "delete", "list", "count"]
_CUSTOM_METHODS = [
    "list_by_owner",
    "count_by_owner",
    "get_by_name_and_owner",
    "list_by_owner_and_status",
    "count_by_owner_and_status",
]


@pytest.mark.unit
class TestIAgentRepository:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            IAgentRepository()  # type: ignore[abstract]

    @pytest.mark.parametrize("method", _CRUD_METHODS + _CUSTOM_METHODS)
    def test_has_required_method(self, method: str) -> None:
        assert hasattr(IAgentRepository, method)
