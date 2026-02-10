"""knowledge 领域事件测试。"""

import pytest

from src.modules.knowledge.domain.events import (
    DocumentIndexedEvent,
    DocumentUploadedEvent,
    KnowledgeBaseActivatedEvent,
    KnowledgeBaseCreatedEvent,
    KnowledgeBaseDeletedEvent,
    KnowledgeBaseSyncStartedEvent,
)
from src.shared.domain.events import DomainEvent


@pytest.mark.unit
class TestKnowledgeBaseEvents:
    def test_created_event(self) -> None:
        event = KnowledgeBaseCreatedEvent(knowledge_base_id=1, owner_id=10)
        assert event.knowledge_base_id == 1
        assert event.owner_id == 10
        assert isinstance(event, DomainEvent)

    def test_activated_event(self) -> None:
        event = KnowledgeBaseActivatedEvent(knowledge_base_id=1)
        assert event.knowledge_base_id == 1

    def test_sync_started_event(self) -> None:
        event = KnowledgeBaseSyncStartedEvent(knowledge_base_id=1)
        assert event.knowledge_base_id == 1

    def test_deleted_event(self) -> None:
        event = KnowledgeBaseDeletedEvent(knowledge_base_id=1, owner_id=10)
        assert event.knowledge_base_id == 1
        assert event.owner_id == 10


@pytest.mark.unit
class TestDocumentEvents:
    def test_uploaded_event(self) -> None:
        event = DocumentUploadedEvent(document_id=1, knowledge_base_id=2, filename="test.pdf")
        assert event.document_id == 1
        assert event.knowledge_base_id == 2
        assert event.filename == "test.pdf"

    def test_indexed_event(self) -> None:
        event = DocumentIndexedEvent(document_id=1, knowledge_base_id=2, chunk_count=42)
        assert event.document_id == 1
        assert event.chunk_count == 42
