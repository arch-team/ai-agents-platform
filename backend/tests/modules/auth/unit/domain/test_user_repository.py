"""IUserRepository 接口单元测试。"""

import pytest

from src.modules.auth.domain.repositories.user_repository import IUserRepository


@pytest.mark.unit
class TestIUserRepository:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            IUserRepository()  # type: ignore[abstract]

    def test_has_get_by_email_method(self) -> None:
        assert hasattr(IUserRepository, "get_by_email")

    def test_has_inherited_crud_methods(self) -> None:
        assert hasattr(IUserRepository, "get_by_id")
        assert hasattr(IUserRepository, "create")
        assert hasattr(IUserRepository, "update")
        assert hasattr(IUserRepository, "delete")
        assert hasattr(IUserRepository, "list")
        assert hasattr(IUserRepository, "count")
