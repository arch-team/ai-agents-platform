"""Knowledge 应用服务。"""

import asyncio

from opentelemetry import trace

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
from src.modules.knowledge.application.interfaces.document_storage import (
    IDocumentStorage,
)
from src.modules.knowledge.application.interfaces.knowledge_service import (
    IKnowledgeService,
)
from src.modules.knowledge.domain.entities.document import Document
from src.modules.knowledge.domain.entities.knowledge_base import KnowledgeBase
from src.modules.knowledge.domain.events import (
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
from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)
from src.shared.application.dtos import PagedResult
from src.shared.application.ownership import check_ownership, get_or_raise
from src.shared.domain.event_bus import event_bus
from src.shared.domain.exceptions import InvalidStateTransitionError


tracer = trace.get_tracer(__name__)

_QUERYABLE_STATUSES: frozenset[KnowledgeBaseStatus] = frozenset(
    {KnowledgeBaseStatus.ACTIVE, KnowledgeBaseStatus.SYNCING},
)


class KnowledgeService:
    """Knowledge 业务服务, 编排知识库 CRUD、文档管理、同步和检索用例。"""

    def __init__(
        self,
        kb_repo: IKnowledgeBaseRepository,
        doc_repo: IDocumentRepository,
        knowledge_svc: IKnowledgeService,
        doc_storage: IDocumentStorage,
    ) -> None:
        self._kb_repo = kb_repo
        self._doc_repo = doc_repo
        self._knowledge_svc = knowledge_svc
        self._doc_storage = doc_storage

    # -- 知识库 CRUD --

    async def create_knowledge_base(
        self,
        dto: CreateKnowledgeBaseDTO,
        owner_id: int,
    ) -> KnowledgeBaseDTO:
        """创建知识库。调用 Bedrock 创建 KB, 激活, 发布事件。

        Raises:
            KnowledgeBaseNameDuplicateError: 同 owner 下名称重复
        """
        await self._check_name_unique(dto.name, owner_id)

        kb = KnowledgeBase(
            name=dto.name,
            description=dto.description,
            owner_id=owner_id,
            agent_id=dto.agent_id,
        )
        created = await self._kb_repo.create(kb)
        if created.id is None:
            msg = "KnowledgeBase 创建后 ID 不能为空"
            raise ValueError(msg)

        # 调用 Bedrock 创建 Knowledge Base
        result = await self._knowledge_svc.create_knowledge_base(
            created.name,
            s3_bucket="",
            s3_prefix=f"kb/{created.id}/",
        )
        created.bedrock_kb_id = result.bedrock_kb_id
        created.s3_prefix = result.s3_prefix
        created.activate()
        updated = await self._kb_repo.update(created)

        await asyncio.gather(
            event_bus.publish_async(
                KnowledgeBaseCreatedEvent(
                    knowledge_base_id=created.id,
                    owner_id=owner_id,
                ),
            ),
            event_bus.publish_async(
                KnowledgeBaseActivatedEvent(knowledge_base_id=created.id),
            ),
        )
        return self._to_kb_dto(updated)

    async def get_knowledge_base(self, kb_id: int, user_id: int) -> KnowledgeBaseDTO:
        """获取知识库详情。校验所有权。

        Raises:
            KnowledgeBaseNotFoundError, DomainError(FORBIDDEN_KNOWLEDGE_BASE)
        """
        kb = await self._get_owned_kb(kb_id, user_id)
        return self._to_kb_dto(kb)

    async def list_knowledge_bases(
        self,
        user_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[KnowledgeBaseDTO]:
        """获取知识库列表。"""
        offset = (page - 1) * page_size
        items, total = await asyncio.gather(
            self._kb_repo.list_by_owner(user_id, offset=offset, limit=page_size),
            self._kb_repo.count_by_owner(user_id),
        )
        return PagedResult(
            items=[self._to_kb_dto(kb) for kb in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_knowledge_base(
        self,
        kb_id: int,
        dto: UpdateKnowledgeBaseDTO,
        user_id: int,
    ) -> KnowledgeBaseDTO:
        """更新知识库。仅 ACTIVE 状态可更新。

        Raises:
            KnowledgeBaseNotFoundError, DomainError(FORBIDDEN_KNOWLEDGE_BASE),
            InvalidStateTransitionError, KnowledgeBaseNameDuplicateError
        """
        kb = await self._get_owned_kb(kb_id, user_id)

        if kb.status != KnowledgeBaseStatus.ACTIVE:
            raise InvalidStateTransitionError(
                entity_type="KnowledgeBase",
                current_state=kb.status.value,
                target_state="update",
            )

        if dto.name is not None and dto.name != kb.name:
            await self._check_name_unique(dto.name, kb.owner_id)
            kb.name = dto.name

        if dto.description is not None:
            kb.description = dto.description

        if dto.agent_id is not None:
            kb.agent_id = dto.agent_id

        kb.touch()
        updated = await self._kb_repo.update(kb)
        return self._to_kb_dto(updated)

    async def delete_knowledge_base(self, kb_id: int, user_id: int) -> None:
        """删除知识库。mark_deleted + 调用 Bedrock 删除 + 发布事件。

        Raises:
            KnowledgeBaseNotFoundError, DomainError(FORBIDDEN_KNOWLEDGE_BASE),
            InvalidStateTransitionError
        """
        kb = await self._get_owned_kb(kb_id, user_id)

        kb.mark_deleted()
        await self._kb_repo.update(kb)
        await self._knowledge_svc.delete_knowledge_base(kb.bedrock_kb_id)

        if kb.id is None:
            msg = "KnowledgeBase ID 不能为空"
            raise ValueError(msg)
        await event_bus.publish_async(
            KnowledgeBaseDeletedEvent(
                knowledge_base_id=kb.id,
                owner_id=user_id,
            ),
        )

    # -- 文档管理 --

    async def upload_document(
        self,
        kb_id: int,
        dto: UploadDocumentDTO,
        user_id: int,
    ) -> DocumentDTO:
        """上传文档。校验 KB 所有权和 ACTIVE 状态。

        Raises:
            KnowledgeBaseNotFoundError, DomainError(FORBIDDEN_KNOWLEDGE_BASE),
            InvalidStateTransitionError
        """
        kb = await self._get_owned_kb(kb_id, user_id)

        if kb.status != KnowledgeBaseStatus.ACTIVE:
            raise InvalidStateTransitionError(
                entity_type="KnowledgeBase",
                current_state=kb.status.value,
                target_state="upload",
            )

        s3_key = f"kb/{kb_id}/{dto.filename}"
        await self._doc_storage.upload(s3_key, dto.content, content_type=dto.content_type)

        doc = Document(
            knowledge_base_id=kb_id,
            filename=dto.filename,
            s3_key=s3_key,
            file_size=len(dto.content),
            content_type=dto.content_type,
        )
        doc.start_processing()
        created = await self._doc_repo.create(doc)
        if created.id is None:
            msg = "Document 创建后 ID 不能为空"
            raise ValueError(msg)

        await event_bus.publish_async(
            DocumentUploadedEvent(
                document_id=created.id,
                knowledge_base_id=kb_id,
                filename=dto.filename,
            ),
        )
        return self._to_doc_dto(created)

    async def list_documents(
        self,
        kb_id: int,
        user_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DocumentDTO], int]:
        """获取文档列表。校验 KB 所有权。"""
        await self._get_owned_kb(kb_id, user_id)

        offset = (page - 1) * page_size
        docs, total = await asyncio.gather(
            self._doc_repo.list_by_knowledge_base(kb_id, offset=offset, limit=page_size),
            self._doc_repo.count_by_knowledge_base(kb_id),
        )
        return [self._to_doc_dto(d) for d in docs], total

    async def delete_document(
        self,
        kb_id: int,
        doc_id: int,
        user_id: int,
    ) -> None:
        """删除文档。校验 KB 所有权。

        Raises:
            KnowledgeBaseNotFoundError, DomainError(FORBIDDEN_KNOWLEDGE_BASE),
            DocumentNotFoundError
        """
        await self._get_owned_kb(kb_id, user_id)

        doc = await self._doc_repo.get_by_id(doc_id)
        if doc is None:
            raise DocumentNotFoundError(doc_id)

        await self._doc_storage.delete(doc.s3_key)
        await self._doc_repo.delete(doc_id)

    # -- 同步和检索 --

    async def sync_knowledge_base(
        self,
        kb_id: int,
        user_id: int,
    ) -> KnowledgeBaseDTO:
        """触发知识库同步。ACTIVE -> SYNCING。

        Raises:
            KnowledgeBaseNotFoundError, DomainError(FORBIDDEN_KNOWLEDGE_BASE),
            InvalidStateTransitionError
        """
        kb = await self._get_owned_kb(kb_id, user_id)

        kb.start_sync()
        updated = await self._kb_repo.update(kb)
        await self._knowledge_svc.start_sync(kb.bedrock_kb_id)

        if kb.id is None:
            msg = "KnowledgeBase ID 不能为空"
            raise ValueError(msg)
        await event_bus.publish_async(
            KnowledgeBaseSyncStartedEvent(knowledge_base_id=kb.id),
        )
        return self._to_kb_dto(updated)

    async def query(
        self,
        kb_id: int,
        dto: QueryRequestDTO,
        user_id: int,
    ) -> QueryResponseDTO:
        """RAG 检索。ACTIVE/SYNCING 状态可检索。

        Raises:
            KnowledgeBaseNotFoundError, DomainError(FORBIDDEN_KNOWLEDGE_BASE),
            InvalidStateTransitionError
        """
        kb = await self._get_owned_kb(kb_id, user_id)

        if kb.status not in _QUERYABLE_STATUSES:
            raise InvalidStateTransitionError(
                entity_type="KnowledgeBase",
                current_state=kb.status.value,
                target_state="query",
            )

        with tracer.start_as_current_span(
            "rag.retrieve",
            attributes={
                "rag.knowledge_base_id": str(kb_id),
                "rag.bedrock_kb_id": kb.bedrock_kb_id,
                "rag.top_k": dto.top_k,
            },
        ):
            chunks = await self._knowledge_svc.retrieve(
                kb.bedrock_kb_id,
                dto.query,
                top_k=dto.top_k,
            )

        if kb.id is None:
            msg = "KnowledgeBase ID 不能为空"
            raise ValueError(msg)
        return QueryResponseDTO(
            results=[
                QueryResultDTO(
                    content=c.content,
                    score=c.score,
                    document_id=c.document_id,
                    metadata=c.metadata or {},
                )
                for c in chunks
            ],
            query=dto.query,
            knowledge_base_id=kb.id,
        )

    # -- 内部辅助 --

    async def _get_kb_or_raise(self, kb_id: int) -> KnowledgeBase:
        return await get_or_raise(self._kb_repo, kb_id, KnowledgeBaseNotFoundError, kb_id)

    async def _get_owned_kb(self, kb_id: int, user_id: int) -> KnowledgeBase:
        """获取知识库并校验所有权。"""
        kb = await self._get_kb_or_raise(kb_id)
        check_ownership(kb, user_id, error_code="FORBIDDEN_KNOWLEDGE_BASE")
        return kb

    async def _check_name_unique(self, name: str, owner_id: int) -> None:
        existing = await self._kb_repo.get_by_name_and_owner(name, owner_id)
        if existing is not None:
            raise KnowledgeBaseNameDuplicateError(name, owner_id)

    @staticmethod
    def _to_kb_dto(kb: KnowledgeBase) -> KnowledgeBaseDTO:
        if kb.id is None or kb.created_at is None or kb.updated_at is None:
            msg = "KnowledgeBase 缺少必要字段 (id/created_at/updated_at)"
            raise ValueError(msg)
        return KnowledgeBaseDTO(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            status=kb.status.value,
            owner_id=kb.owner_id,
            agent_id=kb.agent_id,
            bedrock_kb_id=kb.bedrock_kb_id,
            s3_prefix=kb.s3_prefix,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
        )

    @staticmethod
    def _to_doc_dto(doc: Document) -> DocumentDTO:
        if doc.id is None or doc.created_at is None or doc.updated_at is None:
            msg = "Document 缺少必要字段 (id/created_at/updated_at)"
            raise ValueError(msg)
        return DocumentDTO(
            id=doc.id,
            knowledge_base_id=doc.knowledge_base_id,
            filename=doc.filename,
            s3_key=doc.s3_key,
            file_size=doc.file_size,
            status=doc.status.value,
            content_type=doc.content_type,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
