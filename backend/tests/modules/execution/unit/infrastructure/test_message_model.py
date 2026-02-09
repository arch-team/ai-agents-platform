"""MessageModel ORM 模型单元测试。"""

import pytest

from src.modules.execution.infrastructure.persistence.models.message_model import MessageModel
from src.shared.infrastructure.database import Base


@pytest.mark.unit
class TestMessageModel:
    def test_inherits_base(self) -> None:
        assert issubclass(MessageModel, Base)

    def test_tablename(self) -> None:
        assert MessageModel.__tablename__ == "messages"

    def test_has_required_columns(self) -> None:
        column_names = {c.key for c in MessageModel.__table__.columns}
        expected = {
            "id",
            "conversation_id",
            "role",
            "content",
            "token_count",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(column_names)

    def test_conversation_id_column_is_not_nullable(self) -> None:
        conv_id_col = MessageModel.__table__.columns["conversation_id"]
        assert conv_id_col.nullable is False

    def test_conversation_id_has_foreign_key(self) -> None:
        conv_id_col = MessageModel.__table__.columns["conversation_id"]
        fk_targets = {fk.target_fullname for fk in conv_id_col.foreign_keys}
        assert "conversations.id" in fk_targets

    def test_conversation_id_is_indexed(self) -> None:
        conv_id_col = MessageModel.__table__.columns["conversation_id"]
        assert conv_id_col.index is True

    def test_role_column_is_not_nullable(self) -> None:
        role_col = MessageModel.__table__.columns["role"]
        assert role_col.nullable is False

    def test_content_column_is_not_nullable(self) -> None:
        content_col = MessageModel.__table__.columns["content"]
        assert content_col.nullable is False

    def test_content_has_default(self) -> None:
        content_col = MessageModel.__table__.columns["content"]
        assert content_col.default is not None

    def test_token_count_has_default(self) -> None:
        token_count_col = MessageModel.__table__.columns["token_count"]
        assert token_count_col.default is not None
