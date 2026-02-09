"""UserModel ORM 模型单元测试。"""

import pytest

from src.modules.auth.infrastructure.persistence.models.user_model import UserModel
from src.shared.infrastructure.database import Base


@pytest.mark.unit
class TestUserModel:
    def test_inherits_base(self) -> None:
        assert issubclass(UserModel, Base)

    def test_tablename(self) -> None:
        assert UserModel.__tablename__ == "users"

    def test_has_required_columns(self) -> None:
        column_names = {c.key for c in UserModel.__table__.columns}
        expected = {"id", "email", "hashed_password", "name", "role", "is_active", "created_at", "updated_at"}
        assert expected.issubset(column_names)

    def test_email_column_is_unique(self) -> None:
        email_col = UserModel.__table__.columns["email"]
        assert email_col.unique is True

    def test_email_column_is_not_nullable(self) -> None:
        email_col = UserModel.__table__.columns["email"]
        assert email_col.nullable is False

    def test_role_has_default(self) -> None:
        role_col = UserModel.__table__.columns["role"]
        assert role_col.default is not None

    def test_is_active_has_default(self) -> None:
        is_active_col = UserModel.__table__.columns["is_active"]
        assert is_active_col.default is not None
