"""Knowledge 模块测试配置和 Fixture。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.knowledge.application.interfaces.document_storage import (
    IDocumentStorage,
)
from src.modules.knowledge.application.interfaces.knowledge_service import (
    IKnowledgeService,
)
from src.modules.knowledge.application.services.knowledge_service import (
    KnowledgeService,
)
from src.modules.knowledge.domain.entities.document import Document
from src.modules.knowledge.domain.entities.knowledge_base import KnowledgeBase
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


def make_kb(
    *,
    kb_id: int = 1,
    name: str = "测试知识库",
    description: str = "描述",
    status: KnowledgeBaseStatus = KnowledgeBaseStatus.ACTIVE,
    owner_id: int = 100,
    agent_id: int | None = None,
    bedrock_kb_id: str = "kb-abc123",
    s3_prefix: str = "kb/1/",
) -> KnowledgeBase:
    """创建测试用 KnowledgeBase 实体。"""
    return KnowledgeBase(
        id=kb_id,
        name=name,
        description=description,
        status=status,
        owner_id=owner_id,
        agent_id=agent_id,
        bedrock_kb_id=bedrock_kb_id,
        s3_prefix=s3_prefix,
    )


def make_doc(
    *,
    doc_id: int = 10,
    knowledge_base_id: int = 1,
    filename: str = "test.pdf",
    s3_key: str = "kb/1/test.pdf",
    file_size: int = 1024,
    status: DocumentStatus = DocumentStatus.PROCESSING,
    content_type: str = "application/pdf",
    chunk_count: int = 0,
) -> Document:
    """创建测试用 Document 实体。"""
    return Document(
        id=doc_id,
        knowledge_base_id=knowledge_base_id,
        filename=filename,
        s3_key=s3_key,
        file_size=file_size,
        status=status,
        content_type=content_type,
        chunk_count=chunk_count,
    )


@pytest.fixture
def mock_kb_repo() -> AsyncMock:
    """KnowledgeBase 仓库 Mock。"""
    return AsyncMock(spec=IKnowledgeBaseRepository)


@pytest.fixture
def mock_doc_repo() -> AsyncMock:
    """Document 仓库 Mock。"""
    return AsyncMock(spec=IDocumentRepository)


@pytest.fixture
def mock_knowledge_svc() -> AsyncMock:
    """IKnowledgeService Mock（Bedrock KB 适配器）。"""
    return AsyncMock(spec=IKnowledgeService)


@pytest.fixture
def mock_doc_storage() -> AsyncMock:
    """IDocumentStorage Mock（S3 存储适配器）。"""
    return AsyncMock(spec=IDocumentStorage)


@pytest.fixture
def knowledge_service(
    mock_kb_repo: AsyncMock,
    mock_doc_repo: AsyncMock,
    mock_knowledge_svc: AsyncMock,
    mock_doc_storage: AsyncMock,
) -> KnowledgeService:
    """KnowledgeService 实例（注入所有 mock 依赖）。"""
    return KnowledgeService(
        kb_repo=mock_kb_repo,
        doc_repo=mock_doc_repo,
        knowledge_svc=mock_knowledge_svc,
        doc_storage=mock_doc_storage,
    )


@pytest.fixture
def mock_event_bus():
    """Mock event_bus，自动 patch KnowledgeService 中的 event_bus。"""
    with patch(
        "src.modules.knowledge.application.services.knowledge_service.event_bus"
    ) as mock_bus:
        mock_bus.publish_async = AsyncMock()
        yield mock_bus
