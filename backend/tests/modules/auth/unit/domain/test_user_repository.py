"""IUserRepository 接口单元测试。"""

import pytest

from src.modules.auth.domain.repositories.user_repository import IUserRepository


_CRUD_METHODS = ["get_by_id", "create", "update", "delete", "list", "count"]
_CUSTOM_METHODS = ["get_by_email"]


@pytest.mark.unit
class TestIUserRepository:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            IUserRepository()  # type: ignore[abstract]

    @pytest.mark.parametrize("method", _CRUD_METHODS + _CUSTOM_METHODS)
    def test_has_required_method(self, method: str) -> None:
        assert hasattr(IUserRepository, method)
