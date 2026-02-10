"""知识库领域层。"""

from src.modules.knowledge.domain.entities.document import Document
from src.modules.knowledge.domain.entities.knowledge_base import KnowledgeBase
from src.modules.knowledge.domain.events import (
    DocumentIndexedEvent,
    DocumentUploadedEvent,
    KnowledgeBaseActivatedEvent,
    KnowledgeBaseCreatedEvent,
    KnowledgeBaseDeletedEvent,
    KnowledgeBaseSyncStartedEvent,
)
from src.modules.knowledge.domain.exceptions import (
    DocumentNotFoundError,
    KnowledgeBaseNameDuplicateError,
    KnowledgeBaseNotFoundError,
)
from src.modules.knowledge.domain.repositories.document_repository import (
    IDocumentRepository,
)
from src.modules.knowledge.domain.repositories.knowledge_base_repository import (
    IKnowledgeBaseRepository,
)
from src.modules.knowledge.domain.value_objects.document_status import DocumentStatus
from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)


__all__ = [
    "Document",
    "DocumentIndexedEvent",
    "DocumentNotFoundError",
    "DocumentStatus",
    "DocumentUploadedEvent",
    "IDocumentRepository",
    "IKnowledgeBaseRepository",
    "KnowledgeBase",
    "KnowledgeBaseActivatedEvent",
    "KnowledgeBaseCreatedEvent",
    "KnowledgeBaseDeletedEvent",
    "KnowledgeBaseNameDuplicateError",
    "KnowledgeBaseNotFoundError",
    "KnowledgeBaseStatus",
    "KnowledgeBaseSyncStartedEvent",
]
