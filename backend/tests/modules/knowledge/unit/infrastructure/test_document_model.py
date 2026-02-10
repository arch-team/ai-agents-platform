"""DocumentModel 单元测试。"""

import pytest

from src.modules.knowledge.infrastructure.persistence.models.document_model import DocumentModel


@pytest.mark.unit
class TestDocumentModel:
    def test_tablename(self) -> None:
        assert DocumentModel.__tablename__ == "documents"

    def test_has_required_columns(self) -> None:
        cols = {c.name for c in DocumentModel.__table__.columns}
        expected = {"id", "knowledge_base_id", "filename", "s3_key", "file_size", "status", "content_type", "chunk_count", "created_at", "updated_at"}
        assert expected.issubset(cols)
