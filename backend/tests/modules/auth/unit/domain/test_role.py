"""Role 枚举单元测试。"""

import pytest

from src.modules.auth.domain.value_objects.role import Role


@pytest.mark.unit
class TestRole:
    def test_admin_value(self) -> None:
        assert Role.ADMIN == "admin"

    def test_developer_value(self) -> None:
        assert Role.DEVELOPER == "developer"

    def test_viewer_value(self) -> None:
        assert Role.VIEWER == "viewer"

    def test_is_str_enum(self) -> None:
        assert isinstance(Role.ADMIN, str)

    def test_all_members(self) -> None:
        members = {r.value for r in Role}
        assert members == {"admin", "developer", "viewer"}
