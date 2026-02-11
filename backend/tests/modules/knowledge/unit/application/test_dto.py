"""knowledge DTO 测试。"""

from datetime import UTC, datetime

import pytest

from src.modules.knowledge.application.dto.knowledge_dto import (
    CreateKnowledgeBaseDTO,
    DocumentDTO,
    KnowledgeBaseDTO,
    QueryRequestDTO,
    QueryResponseDTO,
    QueryResultDTO,
    UpdateKnowledgeBaseDTO,
    UploadDocumentDTO,
)
from src.shared.application.dtos import PagedResult


@pytest.mark.unit
class TestCreateKnowledgeBaseDTO:
    def test_minimal(self) -> None:
        dto = CreateKnowledgeBaseDTO(name="test-kb")
        assert dto.name == "test-kb"
        assert dto.description == ""
        assert dto.agent_id is None

    def test_with_all_fields(self) -> None:
        dto = CreateKnowledgeBaseDTO(name="kb", description="desc", agent_id=1)
        assert dto.agent_id == 1


@pytest.mark.unit
class TestUpdateKnowledgeBaseDTO:
    def test_all_none(self) -> None:
        dto = UpdateKnowledgeBaseDTO()
        assert dto.name is None
        assert dto.description is None


@pytest.mark.unit
class TestKnowledgeBaseDTO:
    def test_fields(self) -> None:
        now = datetime.now(UTC)
        dto = KnowledgeBaseDTO(
            id=1, name="kb", description="", status="active",
            owner_id=10, agent_id=None, bedrock_kb_id="kb-123",
            s3_prefix="kb/1/", created_at=now, updated_at=now,
        )
        assert dto.id == 1
        assert dto.status == "active"


@pytest.mark.unit
class TestPagedResult:
    def test_empty(self) -> None:
        dto: PagedResult[KnowledgeBaseDTO] = PagedResult(items=[], total=0, page=1, page_size=20)
        assert dto.total == 0


@pytest.mark.unit
class TestDocumentDTO:
    def test_fields(self) -> None:
        now = datetime.now(UTC)
        dto = DocumentDTO(
            id=1, knowledge_base_id=1, filename="test.pdf",
            s3_key="kb/1/test.pdf", file_size=1024, status="indexed",
            content_type="application/pdf", chunk_count=10,
            created_at=now, updated_at=now,
        )
        assert dto.filename == "test.pdf"


@pytest.mark.unit
class TestUploadDocumentDTO:
    def test_fields(self) -> None:
        dto = UploadDocumentDTO(filename="test.pdf", content=b"data")
        assert dto.content_type == "application/octet-stream"


@pytest.mark.unit
class TestQueryDTO:
    def test_request(self) -> None:
        dto = QueryRequestDTO(query="search term")
        assert dto.top_k == 5

    def test_result(self) -> None:
        result = QueryResultDTO(content="answer", score=0.9)
        assert result.document_id == ""

    def test_response(self) -> None:
        resp = QueryResponseDTO(
            results=[QueryResultDTO(content="a", score=0.9)],
            query="q", knowledge_base_id=1,
        )
        assert len(resp.results) == 1
