"""Document 实体测试。"""

import pytest

from src.modules.knowledge.domain.entities.document import Document
from src.modules.knowledge.domain.value_objects.document_status import DocumentStatus
from src.shared.domain.exceptions import InvalidStateTransitionError


def _make_document(
    *,
    knowledge_base_id: int = 1,
    filename: str = "test.pdf",
    s3_key: str = "kb/1/test.pdf",
    file_size: int = 1024,
    status: DocumentStatus = DocumentStatus.UPLOADING,
    content_type: str = "application/pdf",
    chunk_count: int = 0,
) -> Document:
    return Document(
        knowledge_base_id=knowledge_base_id,
        filename=filename,
        s3_key=s3_key,
        file_size=file_size,
        status=status,
        content_type=content_type,
        chunk_count=chunk_count,
    )


@pytest.mark.unit
class TestDocumentCreation:
    def test_create_with_defaults(self) -> None:
        doc = Document(knowledge_base_id=1, filename="test.pdf")
        assert doc.knowledge_base_id == 1
        assert doc.filename == "test.pdf"
        assert doc.status == DocumentStatus.UPLOADING
        assert doc.s3_key == ""
        assert doc.file_size == 0
        assert doc.content_type == "application/octet-stream"
        assert doc.chunk_count == 0

    def test_create_with_all_fields(self) -> None:
        doc = _make_document()
        assert doc.filename == "test.pdf"
        assert doc.file_size == 1024
        assert doc.content_type == "application/pdf"

    def test_filename_min_length(self) -> None:
        with pytest.raises(Exception):
            Document(knowledge_base_id=1, filename="")


@pytest.mark.unit
class TestDocumentStartProcessing:
    def test_start_processing_from_uploading(self) -> None:
        doc = _make_document()
        doc.start_processing()
        assert doc.status == DocumentStatus.PROCESSING

    def test_start_processing_updates_timestamp(self) -> None:
        doc = _make_document()
        original = doc.updated_at
        doc.start_processing()
        assert doc.updated_at != original

    @pytest.mark.parametrize("status", [DocumentStatus.PROCESSING, DocumentStatus.INDEXED, DocumentStatus.FAILED])
    def test_start_processing_from_invalid_state_raises(self, status: DocumentStatus) -> None:
        doc = _make_document(status=status)
        with pytest.raises(InvalidStateTransitionError):
            doc.start_processing()


@pytest.mark.unit
class TestDocumentCompleteIndexing:
    def test_complete_indexing_from_processing(self) -> None:
        doc = _make_document(status=DocumentStatus.PROCESSING)
        doc.complete_indexing(chunk_count=42)
        assert doc.status == DocumentStatus.INDEXED
        assert doc.chunk_count == 42

    def test_complete_indexing_updates_timestamp(self) -> None:
        doc = _make_document(status=DocumentStatus.PROCESSING)
        original = doc.updated_at
        doc.complete_indexing(chunk_count=10)
        assert doc.updated_at != original

    @pytest.mark.parametrize("status", [DocumentStatus.UPLOADING, DocumentStatus.INDEXED, DocumentStatus.FAILED])
    def test_complete_indexing_from_invalid_state_raises(self, status: DocumentStatus) -> None:
        doc = _make_document(status=status)
        with pytest.raises(InvalidStateTransitionError):
            doc.complete_indexing(chunk_count=10)


@pytest.mark.unit
class TestDocumentFail:
    def test_fail_from_uploading(self) -> None:
        doc = _make_document(status=DocumentStatus.UPLOADING)
        doc.fail()
        assert doc.status == DocumentStatus.FAILED

    def test_fail_from_processing(self) -> None:
        doc = _make_document(status=DocumentStatus.PROCESSING)
        doc.fail()
        assert doc.status == DocumentStatus.FAILED

    def test_fail_updates_timestamp(self) -> None:
        doc = _make_document()
        original = doc.updated_at
        doc.fail()
        assert doc.updated_at != original

    @pytest.mark.parametrize("status", [DocumentStatus.INDEXED, DocumentStatus.FAILED])
    def test_fail_from_invalid_state_raises(self, status: DocumentStatus) -> None:
        doc = _make_document(status=status)
        with pytest.raises(InvalidStateTransitionError):
            doc.fail()
