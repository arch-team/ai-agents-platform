"""KnowledgeService 单元测试。"""

import pytest
from unittest.mock import AsyncMock, patch

from src.modules.knowledge.application.dto.knowledge_dto import (
    CreateKnowledgeBaseDTO,
    QueryRequestDTO,
    UpdateKnowledgeBaseDTO,
    UploadDocumentDTO,
)
from src.modules.knowledge.application.interfaces.document_storage import (
    IDocumentStorage,
)
from src.modules.knowledge.application.interfaces.knowledge_service import (
    IKnowledgeService,
    KBCreateResult,
    KBSyncResult,
    RetrievalChunk,
)
from src.modules.knowledge.application.services.knowledge_service import (
    KnowledgeService,
)
from src.modules.knowledge.domain.entities.document import Document
from src.modules.knowledge.domain.entities.knowledge_base import KnowledgeBase
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
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError


EVENT_BUS_PATH = (
    "src.modules.knowledge.application.services.knowledge_service.event_bus"
)


def _make_kb(
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


def _make_doc(
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


def _make_service(
    kb_repo: AsyncMock,
    doc_repo: AsyncMock,
    knowledge_svc: AsyncMock,
    doc_storage: AsyncMock,
) -> KnowledgeService:
    """创建测试用 KnowledgeService。"""
    return KnowledgeService(
        kb_repo=kb_repo,
        doc_repo=doc_repo,
        knowledge_svc=knowledge_svc,
        doc_storage=doc_storage,
    )


def _create_mocks() -> tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
    """创建所有 Mock 依赖。"""
    kb_repo = AsyncMock(spec=IKnowledgeBaseRepository)
    doc_repo = AsyncMock(spec=IDocumentRepository)
    knowledge_svc = AsyncMock(spec=IKnowledgeService)
    doc_storage = AsyncMock(spec=IDocumentStorage)
    return kb_repo, doc_repo, knowledge_svc, doc_storage


# ── 知识库 CRUD ──


@pytest.mark.unit
class TestCreateKnowledgeBase:
    """create_knowledge_base 测试。"""

    @pytest.mark.asyncio
    async def test_create_success(self) -> None:
        """成功创建知识库 — 调用 Bedrock, 激活, 发布事件。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_name_and_owner.return_value = None
        kb_repo.create.side_effect = lambda kb: _make_kb(
            name=kb.name,
            description=kb.description,
            owner_id=kb.owner_id,
            agent_id=kb.agent_id,
            status=KnowledgeBaseStatus.CREATING,
            bedrock_kb_id="",
            s3_prefix="",
        )
        kb_repo.update.side_effect = lambda kb: kb
        knowledge_svc.create_knowledge_base.return_value = KBCreateResult(
            bedrock_kb_id="kb-new123",
            s3_prefix="prefix/new/",
        )

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = CreateKnowledgeBaseDTO(name="新知识库", description="新描述", agent_id=5)

        # Act
        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.create_knowledge_base(dto, owner_id=100)

        # Assert
        assert result.name == "新知识库"
        assert result.description == "新描述"
        assert result.owner_id == 100
        assert result.status == "active"
        assert result.bedrock_kb_id == "kb-new123"
        assert result.s3_prefix == "prefix/new/"
        kb_repo.create.assert_called_once()
        knowledge_svc.create_knowledge_base.assert_called_once()
        # 创建事件 + 激活事件 = 2 次
        assert mock_bus.publish_async.call_count == 2

    @pytest.mark.asyncio
    async def test_create_duplicate_name_raises(self) -> None:
        """同一 owner 下名称重复 — 抛出 KnowledgeBaseNameDuplicateError。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_name_and_owner.return_value = _make_kb(name="已存在")

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = CreateKnowledgeBaseDTO(name="已存在")

        # Act & Assert
        with pytest.raises(KnowledgeBaseNameDuplicateError):
            await service.create_knowledge_base(dto, owner_id=100)


@pytest.mark.unit
class TestGetKnowledgeBase:
    """get_knowledge_base 测试。"""

    @pytest.mark.asyncio
    async def test_get_success(self) -> None:
        """成功获取知识库。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb()

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act
        result = await service.get_knowledge_base(kb_id=1, user_id=100)

        # Assert
        assert result.id == 1
        assert result.name == "测试知识库"

    @pytest.mark.asyncio
    async def test_get_not_found_raises(self) -> None:
        """知识库不存在 — 抛出 KnowledgeBaseNotFoundError。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = None

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act & Assert
        with pytest.raises(KnowledgeBaseNotFoundError):
            await service.get_knowledge_base(kb_id=999, user_id=100)

    @pytest.mark.asyncio
    async def test_get_forbidden_raises(self) -> None:
        """非所有者访问 — 抛出 DomainError(FORBIDDEN_KNOWLEDGE_BASE)。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(owner_id=100)

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act & Assert
        with pytest.raises(DomainError, match="无权操作此知识库"):
            await service.get_knowledge_base(kb_id=1, user_id=999)


@pytest.mark.unit
class TestListKnowledgeBases:
    """list_knowledge_bases 测试。"""

    @pytest.mark.asyncio
    async def test_list_success(self) -> None:
        """成功分页列表查询。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.list_by_owner.return_value = [_make_kb(kb_id=1), _make_kb(kb_id=2)]
        kb_repo.count_by_owner.return_value = 2

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act
        result = await service.list_knowledge_bases(user_id=100, page=1, page_size=10)

        # Assert
        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 10

    @pytest.mark.asyncio
    async def test_list_empty(self) -> None:
        """空结果返回空列表。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.list_by_owner.return_value = []
        kb_repo.count_by_owner.return_value = 0

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act
        result = await service.list_knowledge_bases(user_id=100)

        # Assert
        assert result.total == 0
        assert result.items == []


@pytest.mark.unit
class TestUpdateKnowledgeBase:
    """update_knowledge_base 测试。"""

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """成功更新知识库名称和描述。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb = _make_kb(status=KnowledgeBaseStatus.ACTIVE)
        kb_repo.get_by_id.return_value = kb
        kb_repo.get_by_name_and_owner.return_value = None
        kb_repo.update.side_effect = lambda k: k

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = UpdateKnowledgeBaseDTO(name="新名称", description="新描述")

        # Act
        result = await service.update_knowledge_base(kb_id=1, dto=dto, user_id=100)

        # Assert
        assert result.name == "新名称"
        assert result.description == "新描述"
        kb_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_non_active_raises(self) -> None:
        """非 ACTIVE 状态更新 — 抛出 InvalidStateTransitionError。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            status=KnowledgeBaseStatus.CREATING,
        )

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = UpdateKnowledgeBaseDTO(name="新名称")

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await service.update_knowledge_base(kb_id=1, dto=dto, user_id=100)

    @pytest.mark.asyncio
    async def test_update_forbidden_raises(self) -> None:
        """非所有者更新 — 抛出 DomainError(FORBIDDEN_KNOWLEDGE_BASE)。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(owner_id=100)

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = UpdateKnowledgeBaseDTO(name="新名称")

        # Act & Assert
        with pytest.raises(DomainError, match="无权操作此知识库"):
            await service.update_knowledge_base(kb_id=1, dto=dto, user_id=999)

    @pytest.mark.asyncio
    async def test_update_duplicate_name_raises(self) -> None:
        """名称变更时重复 — 抛出 KnowledgeBaseNameDuplicateError。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            name="原名称", status=KnowledgeBaseStatus.ACTIVE,
        )
        kb_repo.get_by_name_and_owner.return_value = _make_kb(name="已存在名称")

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = UpdateKnowledgeBaseDTO(name="已存在名称")

        # Act & Assert
        with pytest.raises(KnowledgeBaseNameDuplicateError):
            await service.update_knowledge_base(kb_id=1, dto=dto, user_id=100)


@pytest.mark.unit
class TestDeleteKnowledgeBase:
    """delete_knowledge_base 测试。"""

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """成功删除知识库 — mark_deleted + 调用 Bedrock + 发布事件。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            status=KnowledgeBaseStatus.ACTIVE,
            bedrock_kb_id="kb-del123",
        )
        kb_repo.update.side_effect = lambda kb: kb

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act
        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            await service.delete_knowledge_base(kb_id=1, user_id=100)

        # Assert
        kb_repo.update.assert_called_once()
        knowledge_svc.delete_knowledge_base.assert_called_once_with("kb-del123")
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_forbidden_raises(self) -> None:
        """非所有者删除 — 抛出 DomainError(FORBIDDEN_KNOWLEDGE_BASE)。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(owner_id=100)

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act & Assert
        with pytest.raises(DomainError, match="无权操作此知识库"):
            await service.delete_knowledge_base(kb_id=1, user_id=999)


# ── 文档管理 ──


@pytest.mark.unit
class TestUploadDocument:
    """upload_document 测试。"""

    @pytest.mark.asyncio
    async def test_upload_success(self) -> None:
        """成功上传文档 — S3 上传 + 创建 Document + 发布事件。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            status=KnowledgeBaseStatus.ACTIVE,
        )
        doc_repo.create.side_effect = lambda doc: _make_doc(
            knowledge_base_id=doc.knowledge_base_id,
            filename=doc.filename,
            s3_key=doc.s3_key,
            file_size=doc.file_size,
            content_type=doc.content_type,
            status=DocumentStatus.PROCESSING,
        )

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = UploadDocumentDTO(
            filename="report.pdf",
            content=b"pdf-content",
            content_type="application/pdf",
        )

        # Act
        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.upload_document(kb_id=1, dto=dto, user_id=100)

        # Assert
        assert result.filename == "report.pdf"
        assert result.s3_key == "kb/1/report.pdf"
        assert result.content_type == "application/pdf"
        doc_storage.upload.assert_called_once_with(
            "kb/1/report.pdf",
            b"pdf-content",
            content_type="application/pdf",
        )
        doc_repo.create.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_non_active_kb_raises(self) -> None:
        """知识库非 ACTIVE 状态上传 — 抛出 InvalidStateTransitionError。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            status=KnowledgeBaseStatus.CREATING,
        )

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = UploadDocumentDTO(filename="test.pdf", content=b"data")

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await service.upload_document(kb_id=1, dto=dto, user_id=100)

    @pytest.mark.asyncio
    async def test_upload_forbidden_raises(self) -> None:
        """非所有者上传 — 抛出 DomainError(FORBIDDEN_KNOWLEDGE_BASE)。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(owner_id=100)

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = UploadDocumentDTO(filename="test.pdf", content=b"data")

        # Act & Assert
        with pytest.raises(DomainError, match="无权操作此知识库"):
            await service.upload_document(kb_id=1, dto=dto, user_id=999)


@pytest.mark.unit
class TestListDocuments:
    """list_documents 测试。"""

    @pytest.mark.asyncio
    async def test_list_success(self) -> None:
        """成功列表查询文档。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb()
        doc_repo.list_by_knowledge_base.return_value = [
            _make_doc(doc_id=10),
            _make_doc(doc_id=11),
        ]
        doc_repo.count_by_knowledge_base.return_value = 2

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act
        docs, total = await service.list_documents(kb_id=1, user_id=100)

        # Assert
        assert total == 2
        assert len(docs) == 2

    @pytest.mark.asyncio
    async def test_list_forbidden_raises(self) -> None:
        """非所有者查询文档 — 抛出 DomainError(FORBIDDEN_KNOWLEDGE_BASE)。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(owner_id=100)

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act & Assert
        with pytest.raises(DomainError, match="无权操作此知识库"):
            await service.list_documents(kb_id=1, user_id=999)


@pytest.mark.unit
class TestDeleteDocument:
    """delete_document 测试。"""

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """成功删除文档 — S3 删除 + 数据库删除。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb()
        doc_repo.get_by_id.return_value = _make_doc(
            doc_id=10, s3_key="kb/1/test.pdf",
        )

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act
        await service.delete_document(kb_id=1, doc_id=10, user_id=100)

        # Assert
        doc_storage.delete.assert_called_once_with("kb/1/test.pdf")
        doc_repo.delete.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_delete_doc_not_found_raises(self) -> None:
        """文档不存在 — 抛出 DocumentNotFoundError。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb()
        doc_repo.get_by_id.return_value = None

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act & Assert
        with pytest.raises(DocumentNotFoundError):
            await service.delete_document(kb_id=1, doc_id=999, user_id=100)

    @pytest.mark.asyncio
    async def test_delete_forbidden_raises(self) -> None:
        """非所有者删除文档 — 抛出 DomainError(FORBIDDEN_KNOWLEDGE_BASE)。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(owner_id=100)

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act & Assert
        with pytest.raises(DomainError, match="无权操作此知识库"):
            await service.delete_document(kb_id=1, doc_id=10, user_id=999)


# ── 同步和检索 ──


@pytest.mark.unit
class TestSyncKnowledgeBase:
    """sync_knowledge_base 测试。"""

    @pytest.mark.asyncio
    async def test_sync_success(self) -> None:
        """成功触发同步 — start_sync + 调用 Bedrock + 发布事件。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            status=KnowledgeBaseStatus.ACTIVE,
            bedrock_kb_id="kb-sync123",
        )
        kb_repo.update.side_effect = lambda kb: kb
        knowledge_svc.start_sync.return_value = KBSyncResult(
            ingestion_job_id="job-1", status="IN_PROGRESS",
        )

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act
        with patch(EVENT_BUS_PATH) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.sync_knowledge_base(kb_id=1, user_id=100)

        # Assert
        assert result.status == "syncing"
        knowledge_svc.start_sync.assert_called_once_with("kb-sync123")
        kb_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_non_active_raises(self) -> None:
        """非 ACTIVE 状态同步 — 抛出 InvalidStateTransitionError。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            status=KnowledgeBaseStatus.SYNCING,
        )

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await service.sync_knowledge_base(kb_id=1, user_id=100)

    @pytest.mark.asyncio
    async def test_sync_forbidden_raises(self) -> None:
        """非所有者同步 — 抛出 DomainError(FORBIDDEN_KNOWLEDGE_BASE)。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(owner_id=100)

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)

        # Act & Assert
        with pytest.raises(DomainError, match="无权操作此知识库"):
            await service.sync_knowledge_base(kb_id=1, user_id=999)


@pytest.mark.unit
class TestQuery:
    """query 测试。"""

    @pytest.mark.asyncio
    async def test_query_success(self) -> None:
        """成功检索 — 调用 Bedrock retrieve + 转换结果。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            status=KnowledgeBaseStatus.ACTIVE,
            bedrock_kb_id="kb-query123",
        )
        knowledge_svc.retrieve.return_value = [
            RetrievalChunk(
                content="相关内容",
                score=0.95,
                document_id="doc-1",
                metadata={"source": "test.pdf"},
            ),
        ]

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = QueryRequestDTO(query="测试查询", top_k=3)

        # Act
        result = await service.query(kb_id=1, dto=dto, user_id=100)

        # Assert
        assert result.query == "测试查询"
        assert result.knowledge_base_id == 1
        assert len(result.results) == 1
        assert result.results[0].content == "相关内容"
        assert result.results[0].score == 0.95
        knowledge_svc.retrieve.assert_called_once_with(
            "kb-query123", "测试查询", top_k=3,
        )

    @pytest.mark.asyncio
    async def test_query_syncing_allowed(self) -> None:
        """SYNCING 状态允许检索。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            status=KnowledgeBaseStatus.SYNCING,
            bedrock_kb_id="kb-q2",
        )
        knowledge_svc.retrieve.return_value = []

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = QueryRequestDTO(query="查询")

        # Act
        result = await service.query(kb_id=1, dto=dto, user_id=100)

        # Assert
        assert result.results == []

    @pytest.mark.asyncio
    async def test_query_non_queryable_raises(self) -> None:
        """非 ACTIVE/SYNCING 状态检索 — 抛出 InvalidStateTransitionError。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(
            status=KnowledgeBaseStatus.CREATING,
        )

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = QueryRequestDTO(query="查询")

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await service.query(kb_id=1, dto=dto, user_id=100)

    @pytest.mark.asyncio
    async def test_query_forbidden_raises(self) -> None:
        """非所有者检索 — 抛出 DomainError(FORBIDDEN_KNOWLEDGE_BASE)。"""
        # Arrange
        kb_repo, doc_repo, knowledge_svc, doc_storage = _create_mocks()
        kb_repo.get_by_id.return_value = _make_kb(owner_id=100)

        service = _make_service(kb_repo, doc_repo, knowledge_svc, doc_storage)
        dto = QueryRequestDTO(query="查询")

        # Act & Assert
        with pytest.raises(DomainError, match="无权操作此知识库"):
            await service.query(kb_id=1, dto=dto, user_id=999)
