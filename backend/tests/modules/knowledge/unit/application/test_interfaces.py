"""knowledge 外部服务接口测试。"""

import pytest

from src.modules.knowledge.application.interfaces.document_storage import IDocumentStorage
from src.modules.knowledge.application.interfaces.knowledge_service import (
    IKnowledgeService,
    KBCreateResult,
    KBSyncResult,
    RetrievalChunk,
)


@pytest.mark.unit
class TestIKnowledgeService:
    def test_has_create_method(self) -> None:
        assert hasattr(IKnowledgeService, "create_knowledge_base")

    def test_has_delete_method(self) -> None:
        assert hasattr(IKnowledgeService, "delete_knowledge_base")

    def test_has_start_sync_method(self) -> None:
        assert hasattr(IKnowledgeService, "start_sync")

    def test_has_retrieve_method(self) -> None:
        assert hasattr(IKnowledgeService, "retrieve")


@pytest.mark.unit
class TestIDocumentStorage:
    def test_has_upload_method(self) -> None:
        assert hasattr(IDocumentStorage, "upload")

    def test_has_delete_method(self) -> None:
        assert hasattr(IDocumentStorage, "delete")

    def test_has_get_presigned_url_method(self) -> None:
        assert hasattr(IDocumentStorage, "get_presigned_url")


@pytest.mark.unit
class TestDataStructures:
    def test_kb_create_result(self) -> None:
        result = KBCreateResult(bedrock_kb_id="kb-123", s3_prefix="kb/1/")
        assert result.bedrock_kb_id == "kb-123"
        assert result.s3_prefix == "kb/1/"

    def test_kb_sync_result(self) -> None:
        result = KBSyncResult(ingestion_job_id="job-456", status="IN_PROGRESS")
        assert result.ingestion_job_id == "job-456"

    def test_retrieval_chunk(self) -> None:
        chunk = RetrievalChunk(content="test content", score=0.95, document_id="doc-1")
        assert chunk.content == "test content"
        assert chunk.score == 0.95
        assert chunk.document_id == "doc-1"
