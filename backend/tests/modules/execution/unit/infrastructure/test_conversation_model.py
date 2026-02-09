"""ConversationModel ORM 模型单元测试。"""

import pytest

from src.modules.execution.infrastructure.persistence.models.conversation_model import (
    ConversationModel,
)
from src.shared.infrastructure.database import Base


@pytest.mark.unit
class TestConversationModel:
    def test_inherits_base(self) -> None:
        assert issubclass(ConversationModel, Base)

    def test_tablename(self) -> None:
        assert ConversationModel.__tablename__ == "conversations"

    def test_has_required_columns(self) -> None:
        column_names = {c.key for c in ConversationModel.__table__.columns}
        expected = {
            "id",
            "title",
            "agent_id",
            "user_id",
            "status",
            "message_count",
            "total_tokens",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(column_names)

    def test_title_column_is_not_nullable(self) -> None:
        title_col = ConversationModel.__table__.columns["title"]
        assert title_col.nullable is False

    def test_agent_id_column_is_not_nullable(self) -> None:
        agent_id_col = ConversationModel.__table__.columns["agent_id"]
        assert agent_id_col.nullable is False

    def test_agent_id_has_foreign_key(self) -> None:
        agent_id_col = ConversationModel.__table__.columns["agent_id"]
        fk_targets = {fk.target_fullname for fk in agent_id_col.foreign_keys}
        assert "agents.id" in fk_targets

    def test_agent_id_is_indexed(self) -> None:
        agent_id_col = ConversationModel.__table__.columns["agent_id"]
        assert agent_id_col.index is True

    def test_user_id_column_is_not_nullable(self) -> None:
        user_id_col = ConversationModel.__table__.columns["user_id"]
        assert user_id_col.nullable is False

    def test_user_id_has_foreign_key(self) -> None:
        user_id_col = ConversationModel.__table__.columns["user_id"]
        fk_targets = {fk.target_fullname for fk in user_id_col.foreign_keys}
        assert "users.id" in fk_targets

    def test_user_id_is_indexed(self) -> None:
        user_id_col = ConversationModel.__table__.columns["user_id"]
        assert user_id_col.index is True

    def test_status_has_default(self) -> None:
        status_col = ConversationModel.__table__.columns["status"]
        assert status_col.default is not None

    def test_message_count_has_default(self) -> None:
        message_count_col = ConversationModel.__table__.columns["message_count"]
        assert message_count_col.default is not None

    def test_total_tokens_has_default(self) -> None:
        total_tokens_col = ConversationModel.__table__.columns["total_tokens"]
        assert total_tokens_col.default is not None
