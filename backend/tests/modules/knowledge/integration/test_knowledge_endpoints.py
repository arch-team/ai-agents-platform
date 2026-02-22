"""Knowledge API 端点集成测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.knowledge.api.dependencies import get_knowledge_service
from src.modules.knowledge.application.dto.knowledge_dto import (
    DocumentDTO,
    KnowledgeBaseDTO,
    QueryResponseDTO,
    QueryResultDTO,
)
from src.modules.knowledge.domain.exceptions import (
    KnowledgeBaseNameDuplicateError,
    KnowledgeBaseNotFoundError,
)
from src.presentation.api.main import create_app
from src.shared.application.dtos import PagedResult


def _make_user() -> UserDTO:
    return UserDTO(id=1, email="test@example.com", name="Test", role="developer", is_active=True)


def _now() -> datetime:
    return datetime.now(UTC)


def _make_kb_dto(kb_id: int = 1, name: str = "test-kb") -> KnowledgeBaseDTO:
    now = _now()
    return KnowledgeBaseDTO(
        id=kb_id, name=name, description="", status="active",
        owner_id=1, agent_id=None, bedrock_kb_id="kb-123", s3_prefix="kb/1/",
        created_at=now, updated_at=now,
    )


def _make_doc_dto(doc_id: int = 10) -> DocumentDTO:
    now = _now()
    return DocumentDTO(
        id=doc_id, knowledge_base_id=1, filename="test.pdf",
        s3_key="kb/1/test.pdf", file_size=1024, status="indexed",
        content_type="application/pdf", chunk_count=5,
        created_at=now, updated_at=now,
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(mock_service: AsyncMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    app.dependency_overrides[get_knowledge_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.integration
class TestKnowledgeBaseEndpoints:
    def test_create(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.create_knowledge_base.return_value = _make_kb_dto()
        resp = client.post("/api/v1/knowledge-bases", json={"name": "new-kb"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "test-kb"

    def test_create_duplicate_returns_409(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.create_knowledge_base.side_effect = KnowledgeBaseNameDuplicateError("dup", 1)
        resp = client.post("/api/v1/knowledge-bases", json={"name": "dup"})
        assert resp.status_code == 409

    def test_list(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_knowledge_bases.return_value = PagedResult(
            items=[_make_kb_dto()], total=1, page=1, page_size=20,
        )
        resp = client.get("/api/v1/knowledge-bases")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_get(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_knowledge_base.return_value = _make_kb_dto()
        resp = client.get("/api/v1/knowledge-bases/1")
        assert resp.status_code == 200

    def test_get_not_found_returns_404(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_knowledge_base.side_effect = KnowledgeBaseNotFoundError(999)
        resp = client.get("/api/v1/knowledge-bases/999")
        assert resp.status_code == 404

    def test_update(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.update_knowledge_base.return_value = _make_kb_dto(name="updated")
        resp = client.put("/api/v1/knowledge-bases/1", json={"name": "updated"})
        assert resp.status_code == 200

    def test_delete(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.delete_knowledge_base.return_value = None
        resp = client.delete("/api/v1/knowledge-bases/1")
        assert resp.status_code == 204


@pytest.mark.integration
class TestDocumentEndpoints:
    def test_list_documents(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_documents.return_value = ([_make_doc_dto()], 1)
        resp = client.get("/api/v1/knowledge-bases/1/documents")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_delete_document(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.delete_document.return_value = None
        resp = client.delete("/api/v1/knowledge-bases/1/documents/10")
        assert resp.status_code == 204


@pytest.mark.integration
class TestSyncAndQuery:
    def test_sync(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.sync_knowledge_base.return_value = _make_kb_dto()
        resp = client.post("/api/v1/knowledge-bases/1/sync")
        assert resp.status_code == 200

    def test_query(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.query.return_value = QueryResponseDTO(
            results=[QueryResultDTO(content="answer", score=0.9)],
            query="test", knowledge_base_id=1,
        )
        resp = client.post("/api/v1/knowledge-bases/1/query", json={"query": "test"})
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 1
