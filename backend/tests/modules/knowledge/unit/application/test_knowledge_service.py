"""KnowledgeService 单元测试。"""

import pytest
from unittest.mock import AsyncMock

from src.modules.knowledge.application.dto.knowledge_dto import (
    CreateKnowledgeBaseDTO,
    QueryRequestDTO,
    UpdateKnowledgeBaseDTO,
    UploadDocumentDTO,
)
from src.modules.knowledge.application.interfaces.knowledge_service import (
    KBCreateResult,
    KBSyncResult,
    RetrievalChunk,
)
from src.modules.knowledge.application.services.knowledge_service import (
    KnowledgeService,
)
from src.modules.knowledge.domain.exceptions import (
    DocumentNotFoundError,
    KnowledgeBaseNameDuplicateError,
    KnowledgeBaseNotFoundError,
)
from src.modules.knowledge.domain.value_objects.document_status import DocumentStatus
from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError

from tests.modules.knowledge.conftest import make_doc, make_kb


# ── 知识库 CRUD ──


@pytest.mark.unit
class TestCreateKnowledgeBase:
    @pytest.mark.asyncio
    async def test_create_success(
        self,
        mock_kb_repo: AsyncMock,
        mock_knowledge_svc: AsyncMock,
        knowledge_service: KnowledgeService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_kb_repo.get_by_name_and_owner.return_value = None
        mock_kb_repo.create.side_effect = lambda kb: make_kb(
            name=kb.name,
            description=kb.description,
            owner_id=kb.owner_id,
            agent_id=kb.agent_id,
            status=KnowledgeBaseStatus.CREATING,
            bedrock_kb_id="",
            s3_prefix="",
        )
        mock_kb_repo.update.side_effect = lambda kb: kb
        mock_knowledge_svc.create_knowledge_base.return_value = KBCreateResult(
            bedrock_kb_id="kb-new123",
            s3_prefix="prefix/new/",
        )

        dto = CreateKnowledgeBaseDTO(name="新知识库", description="新描述", agent_id=5)
        result = await knowledge_service.create_knowledge_base(dto, owner_id=100)

        assert result.name == "新知识库"
        assert result.description == "新描述"
        assert result.owner_id == 100
        assert result.status == "active"
        assert result.bedrock_kb_id == "kb-new123"
        assert result.s3_prefix == "prefix/new/"
        mock_kb_repo.create.assert_called_once()
        mock_knowledge_svc.create_knowledge_base.assert_called_once()
        # 创建事件 + 激活事件 = 2 次
        assert mock_event_bus.publish_async.call_count == 2

    @pytest.mark.asyncio
    async def test_create_duplicate_name_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_name_and_owner.return_value = make_kb(name="已存在")

        dto = CreateKnowledgeBaseDTO(name="已存在")

        with pytest.raises(KnowledgeBaseNameDuplicateError):
            await knowledge_service.create_knowledge_base(dto, owner_id=100)


@pytest.mark.unit
class TestGetKnowledgeBase:
    @pytest.mark.asyncio
    async def test_get_success(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb()

        result = await knowledge_service.get_knowledge_base(kb_id=1, user_id=100)

        assert result.id == 1
        assert result.name == "测试知识库"

    @pytest.mark.asyncio
    async def test_get_not_found_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = None

        with pytest.raises(KnowledgeBaseNotFoundError):
            await knowledge_service.get_knowledge_base(kb_id=999, user_id=100)

    @pytest.mark.asyncio
    async def test_get_forbidden_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(owner_id=100)

        with pytest.raises(DomainError, match="无权操作此知识库"):
            await knowledge_service.get_knowledge_base(kb_id=1, user_id=999)


@pytest.mark.unit
class TestListKnowledgeBases:
    @pytest.mark.asyncio
    async def test_list_success(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.list_by_owner.return_value = [make_kb(kb_id=1), make_kb(kb_id=2)]
        mock_kb_repo.count_by_owner.return_value = 2

        result = await knowledge_service.list_knowledge_bases(user_id=100, page=1, page_size=10)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 10

    @pytest.mark.asyncio
    async def test_list_empty(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.list_by_owner.return_value = []
        mock_kb_repo.count_by_owner.return_value = 0

        result = await knowledge_service.list_knowledge_bases(user_id=100)

        assert result.total == 0
        assert result.items == []


@pytest.mark.unit
class TestUpdateKnowledgeBase:
    @pytest.mark.asyncio
    async def test_update_success(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(status=KnowledgeBaseStatus.ACTIVE)
        mock_kb_repo.get_by_name_and_owner.return_value = None
        mock_kb_repo.update.side_effect = lambda k: k

        dto = UpdateKnowledgeBaseDTO(name="新名称", description="新描述")
        result = await knowledge_service.update_knowledge_base(kb_id=1, dto=dto, user_id=100)

        assert result.name == "新名称"
        assert result.description == "新描述"
        mock_kb_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_non_active_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(status=KnowledgeBaseStatus.CREATING)

        dto = UpdateKnowledgeBaseDTO(name="新名称")

        with pytest.raises(InvalidStateTransitionError):
            await knowledge_service.update_knowledge_base(kb_id=1, dto=dto, user_id=100)

    @pytest.mark.asyncio
    async def test_update_forbidden_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(owner_id=100)

        dto = UpdateKnowledgeBaseDTO(name="新名称")

        with pytest.raises(DomainError, match="无权操作此知识库"):
            await knowledge_service.update_knowledge_base(kb_id=1, dto=dto, user_id=999)

    @pytest.mark.asyncio
    async def test_update_duplicate_name_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(
            name="原名称", status=KnowledgeBaseStatus.ACTIVE,
        )
        mock_kb_repo.get_by_name_and_owner.return_value = make_kb(name="已存在名称")

        dto = UpdateKnowledgeBaseDTO(name="已存在名称")

        with pytest.raises(KnowledgeBaseNameDuplicateError):
            await knowledge_service.update_knowledge_base(kb_id=1, dto=dto, user_id=100)


@pytest.mark.unit
class TestDeleteKnowledgeBase:
    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        mock_kb_repo: AsyncMock,
        mock_knowledge_svc: AsyncMock,
        knowledge_service: KnowledgeService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(
            status=KnowledgeBaseStatus.ACTIVE,
            bedrock_kb_id="kb-del123",
        )
        mock_kb_repo.update.side_effect = lambda kb: kb

        await knowledge_service.delete_knowledge_base(kb_id=1, user_id=100)

        mock_kb_repo.update.assert_called_once()
        mock_knowledge_svc.delete_knowledge_base.assert_called_once_with("kb-del123")
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_forbidden_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(owner_id=100)

        with pytest.raises(DomainError, match="无权操作此知识库"):
            await knowledge_service.delete_knowledge_base(kb_id=1, user_id=999)


# ── 文档管理 ──


@pytest.mark.unit
class TestUploadDocument:
    @pytest.mark.asyncio
    async def test_upload_success(
        self,
        mock_kb_repo: AsyncMock,
        mock_doc_repo: AsyncMock,
        mock_doc_storage: AsyncMock,
        knowledge_service: KnowledgeService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(status=KnowledgeBaseStatus.ACTIVE)
        mock_doc_repo.create.side_effect = lambda doc: make_doc(
            knowledge_base_id=doc.knowledge_base_id,
            filename=doc.filename,
            s3_key=doc.s3_key,
            file_size=doc.file_size,
            content_type=doc.content_type,
            status=DocumentStatus.PROCESSING,
        )

        dto = UploadDocumentDTO(
            filename="report.pdf",
            content=b"pdf-content",
            content_type="application/pdf",
        )
        result = await knowledge_service.upload_document(kb_id=1, dto=dto, user_id=100)

        assert result.filename == "report.pdf"
        assert result.s3_key == "kb/1/report.pdf"
        assert result.content_type == "application/pdf"
        mock_doc_storage.upload.assert_called_once_with(
            "kb/1/report.pdf",
            b"pdf-content",
            content_type="application/pdf",
        )
        mock_doc_repo.create.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_non_active_kb_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(status=KnowledgeBaseStatus.CREATING)

        dto = UploadDocumentDTO(filename="test.pdf", content=b"data")

        with pytest.raises(InvalidStateTransitionError):
            await knowledge_service.upload_document(kb_id=1, dto=dto, user_id=100)

    @pytest.mark.asyncio
    async def test_upload_forbidden_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(owner_id=100)

        dto = UploadDocumentDTO(filename="test.pdf", content=b"data")

        with pytest.raises(DomainError, match="无权操作此知识库"):
            await knowledge_service.upload_document(kb_id=1, dto=dto, user_id=999)


@pytest.mark.unit
class TestListDocuments:
    @pytest.mark.asyncio
    async def test_list_success(
        self,
        mock_kb_repo: AsyncMock,
        mock_doc_repo: AsyncMock,
        knowledge_service: KnowledgeService,
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb()
        mock_doc_repo.list_by_knowledge_base.return_value = [
            make_doc(doc_id=10),
            make_doc(doc_id=11),
        ]
        mock_doc_repo.count_by_knowledge_base.return_value = 2

        docs, total = await knowledge_service.list_documents(kb_id=1, user_id=100)

        assert total == 2
        assert len(docs) == 2

    @pytest.mark.asyncio
    async def test_list_forbidden_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(owner_id=100)

        with pytest.raises(DomainError, match="无权操作此知识库"):
            await knowledge_service.list_documents(kb_id=1, user_id=999)


@pytest.mark.unit
class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        mock_kb_repo: AsyncMock,
        mock_doc_repo: AsyncMock,
        mock_doc_storage: AsyncMock,
        knowledge_service: KnowledgeService,
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb()
        mock_doc_repo.get_by_id.return_value = make_doc(doc_id=10, s3_key="kb/1/test.pdf")

        await knowledge_service.delete_document(kb_id=1, doc_id=10, user_id=100)

        mock_doc_storage.delete.assert_called_once_with("kb/1/test.pdf")
        mock_doc_repo.delete.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_delete_doc_not_found_raises(
        self,
        mock_kb_repo: AsyncMock,
        mock_doc_repo: AsyncMock,
        knowledge_service: KnowledgeService,
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb()
        mock_doc_repo.get_by_id.return_value = None

        with pytest.raises(DocumentNotFoundError):
            await knowledge_service.delete_document(kb_id=1, doc_id=999, user_id=100)

    @pytest.mark.asyncio
    async def test_delete_forbidden_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(owner_id=100)

        with pytest.raises(DomainError, match="无权操作此知识库"):
            await knowledge_service.delete_document(kb_id=1, doc_id=10, user_id=999)


# ── 同步和检索 ──


@pytest.mark.unit
class TestSyncKnowledgeBase:
    @pytest.mark.asyncio
    async def test_sync_success(
        self,
        mock_kb_repo: AsyncMock,
        mock_knowledge_svc: AsyncMock,
        knowledge_service: KnowledgeService,
        mock_event_bus: AsyncMock,
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(
            status=KnowledgeBaseStatus.ACTIVE,
            bedrock_kb_id="kb-sync123",
        )
        mock_kb_repo.update.side_effect = lambda kb: kb
        mock_knowledge_svc.start_sync.return_value = KBSyncResult(
            ingestion_job_id="job-1", status="IN_PROGRESS",
        )

        result = await knowledge_service.sync_knowledge_base(kb_id=1, user_id=100)

        assert result.status == "syncing"
        mock_knowledge_svc.start_sync.assert_called_once_with("kb-sync123")
        mock_kb_repo.update.assert_called_once()
        mock_event_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_non_active_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(status=KnowledgeBaseStatus.SYNCING)

        with pytest.raises(InvalidStateTransitionError):
            await knowledge_service.sync_knowledge_base(kb_id=1, user_id=100)

    @pytest.mark.asyncio
    async def test_sync_forbidden_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(owner_id=100)

        with pytest.raises(DomainError, match="无权操作此知识库"):
            await knowledge_service.sync_knowledge_base(kb_id=1, user_id=999)


@pytest.mark.unit
class TestQuery:
    @pytest.mark.asyncio
    async def test_query_success(
        self,
        mock_kb_repo: AsyncMock,
        mock_knowledge_svc: AsyncMock,
        knowledge_service: KnowledgeService,
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(
            status=KnowledgeBaseStatus.ACTIVE,
            bedrock_kb_id="kb-query123",
        )
        mock_knowledge_svc.retrieve.return_value = [
            RetrievalChunk(
                content="相关内容",
                score=0.95,
                document_id="doc-1",
                metadata={"source": "test.pdf"},
            ),
        ]

        dto = QueryRequestDTO(query="测试查询", top_k=3)
        result = await knowledge_service.query(kb_id=1, dto=dto, user_id=100)

        assert result.query == "测试查询"
        assert result.knowledge_base_id == 1
        assert len(result.results) == 1
        assert result.results[0].content == "相关内容"
        assert result.results[0].score == 0.95
        mock_knowledge_svc.retrieve.assert_called_once_with(
            "kb-query123", "测试查询", top_k=3,
        )

    @pytest.mark.asyncio
    async def test_query_syncing_allowed(
        self,
        mock_kb_repo: AsyncMock,
        mock_knowledge_svc: AsyncMock,
        knowledge_service: KnowledgeService,
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(
            status=KnowledgeBaseStatus.SYNCING,
            bedrock_kb_id="kb-q2",
        )
        mock_knowledge_svc.retrieve.return_value = []

        dto = QueryRequestDTO(query="查询")
        result = await knowledge_service.query(kb_id=1, dto=dto, user_id=100)

        assert result.results == []

    @pytest.mark.asyncio
    async def test_query_non_queryable_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(status=KnowledgeBaseStatus.CREATING)

        dto = QueryRequestDTO(query="查询")

        with pytest.raises(InvalidStateTransitionError):
            await knowledge_service.query(kb_id=1, dto=dto, user_id=100)

    @pytest.mark.asyncio
    async def test_query_forbidden_raises(
        self, mock_kb_repo: AsyncMock, knowledge_service: KnowledgeService
    ) -> None:
        mock_kb_repo.get_by_id.return_value = make_kb(owner_id=100)

        dto = QueryRequestDTO(query="查询")

        with pytest.raises(DomainError, match="无权操作此知识库"):
            await knowledge_service.query(kb_id=1, dto=dto, user_id=999)
