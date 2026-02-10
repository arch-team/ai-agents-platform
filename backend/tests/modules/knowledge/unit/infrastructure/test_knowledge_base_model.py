"""KnowledgeBaseModel 单元测试。"""

import pytest

from src.modules.knowledge.infrastructure.persistence.models.knowledge_base_model import KnowledgeBaseModel


@pytest.mark.unit
class TestKnowledgeBaseModel:
    def test_tablename(self) -> None:
        assert KnowledgeBaseModel.__tablename__ == "knowledge_bases"

    def test_has_required_columns(self) -> None:
        cols = {c.name for c in KnowledgeBaseModel.__table__.columns}
        expected = {"id", "name", "description", "status", "owner_id", "agent_id", "bedrock_kb_id", "s3_prefix", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_unique_constraint(self) -> None:
        constraints = [c.name for c in KnowledgeBaseModel.__table__.constraints if hasattr(c, "name") and c.name]
        assert "uq_knowledge_bases_owner_name" in constraints
