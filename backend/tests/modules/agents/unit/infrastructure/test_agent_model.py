"""AgentModel ORM 模型单元测试。"""

import pytest

from src.modules.agents.infrastructure.persistence.models.agent_model import AgentModel
from src.shared.infrastructure.database import Base


@pytest.mark.unit
class TestAgentModel:
    def test_inherits_base(self) -> None:
        assert issubclass(AgentModel, Base)

    def test_tablename(self) -> None:
        assert AgentModel.__tablename__ == "agents"

    def test_has_required_columns(self) -> None:
        column_names = {c.key for c in AgentModel.__table__.columns}
        expected = {
            "id",
            "name",
            "description",
            "system_prompt",
            "status",
            "owner_id",
            "model_id",
            "temperature",
            "max_tokens",
            "top_p",
            "stop_sequences",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(column_names)

    def test_name_column_is_not_nullable(self) -> None:
        name_col = AgentModel.__table__.columns["name"]
        assert name_col.nullable is False

    def test_owner_id_column_is_not_nullable(self) -> None:
        owner_id_col = AgentModel.__table__.columns["owner_id"]
        assert owner_id_col.nullable is False

    def test_owner_id_has_foreign_key(self) -> None:
        owner_id_col = AgentModel.__table__.columns["owner_id"]
        fk_targets = {fk.target_fullname for fk in owner_id_col.foreign_keys}
        assert "users.id" in fk_targets

    def test_owner_id_is_indexed(self) -> None:
        owner_id_col = AgentModel.__table__.columns["owner_id"]
        assert owner_id_col.index is True

    def test_status_has_default(self) -> None:
        status_col = AgentModel.__table__.columns["status"]
        assert status_col.default is not None

    def test_model_id_has_default(self) -> None:
        model_id_col = AgentModel.__table__.columns["model_id"]
        assert model_id_col.default is not None

    def test_temperature_has_default(self) -> None:
        temperature_col = AgentModel.__table__.columns["temperature"]
        assert temperature_col.default is not None

    def test_max_tokens_has_default(self) -> None:
        max_tokens_col = AgentModel.__table__.columns["max_tokens"]
        assert max_tokens_col.default is not None

    def test_unique_constraint_owner_name(self) -> None:
        constraint_names = {
            c.name for c in AgentModel.__table__.constraints if hasattr(c, "name") and c.name
        }
        assert "uq_agents_owner_name" in constraint_names
