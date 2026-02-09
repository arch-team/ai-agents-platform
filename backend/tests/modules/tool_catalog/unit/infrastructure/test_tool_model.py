"""ToolModel ORM 模型单元测试。"""

import pytest

from src.modules.tool_catalog.infrastructure.persistence.models.tool_model import ToolModel
from src.shared.infrastructure.database import Base


@pytest.mark.unit
class TestToolModelStructure:
    def test_inherits_base(self) -> None:
        assert issubclass(ToolModel, Base)

    def test_tablename(self) -> None:
        assert ToolModel.__tablename__ == "tools"

    def test_has_required_columns(self) -> None:
        column_names = {c.key for c in ToolModel.__table__.columns}
        expected = {
            "id",
            "name",
            "description",
            "tool_type",
            "version",
            "status",
            "creator_id",
            "server_url",
            "transport",
            "endpoint_url",
            "method",
            "headers",
            "runtime",
            "handler",
            "code_uri",
            "auth_type",
            "auth_config",
            "allowed_roles",
            "reviewer_id",
            "review_comment",
            "reviewed_at",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(column_names)


@pytest.mark.unit
class TestToolModelColumns:
    def test_name_column_is_not_nullable(self) -> None:
        name_col = ToolModel.__table__.columns["name"]
        assert name_col.nullable is False

    def test_tool_type_column_is_not_nullable(self) -> None:
        tool_type_col = ToolModel.__table__.columns["tool_type"]
        assert tool_type_col.nullable is False

    def test_creator_id_column_is_not_nullable(self) -> None:
        creator_id_col = ToolModel.__table__.columns["creator_id"]
        assert creator_id_col.nullable is False

    def test_creator_id_has_foreign_key(self) -> None:
        creator_id_col = ToolModel.__table__.columns["creator_id"]
        fk_targets = {fk.target_fullname for fk in creator_id_col.foreign_keys}
        assert "users.id" in fk_targets

    def test_creator_id_is_indexed(self) -> None:
        creator_id_col = ToolModel.__table__.columns["creator_id"]
        assert creator_id_col.index is True

    def test_status_is_indexed(self) -> None:
        status_col = ToolModel.__table__.columns["status"]
        assert status_col.index is True

    def test_reviewer_id_is_nullable(self) -> None:
        reviewer_id_col = ToolModel.__table__.columns["reviewer_id"]
        assert reviewer_id_col.nullable is True

    def test_reviewer_id_has_foreign_key(self) -> None:
        reviewer_id_col = ToolModel.__table__.columns["reviewer_id"]
        fk_targets = {fk.target_fullname for fk in reviewer_id_col.foreign_keys}
        assert "users.id" in fk_targets

    def test_reviewed_at_is_nullable(self) -> None:
        reviewed_at_col = ToolModel.__table__.columns["reviewed_at"]
        assert reviewed_at_col.nullable is True


@pytest.mark.unit
class TestToolModelDefaults:
    def test_status_has_default(self) -> None:
        status_col = ToolModel.__table__.columns["status"]
        assert status_col.default is not None

    def test_version_has_default(self) -> None:
        version_col = ToolModel.__table__.columns["version"]
        assert version_col.default is not None

    def test_transport_has_default(self) -> None:
        transport_col = ToolModel.__table__.columns["transport"]
        assert transport_col.default is not None

    def test_method_has_default(self) -> None:
        method_col = ToolModel.__table__.columns["method"]
        assert method_col.default is not None

    def test_auth_type_has_default(self) -> None:
        auth_type_col = ToolModel.__table__.columns["auth_type"]
        assert auth_type_col.default is not None

    def test_allowed_roles_has_default(self) -> None:
        allowed_roles_col = ToolModel.__table__.columns["allowed_roles"]
        assert allowed_roles_col.default is not None


@pytest.mark.unit
class TestToolModelConstraints:
    def test_unique_constraint_creator_name(self) -> None:
        constraint_names = {
            c.name for c in ToolModel.__table__.constraints if hasattr(c, "name") and c.name
        }
        assert "uq_tools_creator_name" in constraint_names

    def test_composite_index_status_type(self) -> None:
        index_names = {idx.name for idx in ToolModel.__table__.indexes}
        assert "ix_tools_status_type" in index_names
