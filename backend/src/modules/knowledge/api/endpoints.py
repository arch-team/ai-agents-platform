"""Knowledge API 端点。"""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, status

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.knowledge.api.dependencies import get_knowledge_service
from src.modules.knowledge.api.schemas.requests import (
    CreateKnowledgeBaseRequest,
    QueryRequest,
    UpdateKnowledgeBaseRequest,
)
from src.modules.knowledge.api.schemas.responses import (
    DocumentListResponse,
    DocumentResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
    QueryResponse,
    QueryResultResponse,
)
from src.modules.knowledge.application.dto.knowledge_dto import (
    CreateKnowledgeBaseDTO,
    DocumentDTO,
    KnowledgeBaseDTO,
    QueryRequestDTO,
    UpdateKnowledgeBaseDTO,
    UploadDocumentDTO,
)
from src.modules.knowledge.application.services.knowledge_service import KnowledgeService
from src.shared.api.schemas import calc_total_pages


router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge-bases"])

ServiceDep = Annotated[KnowledgeService, Depends(get_knowledge_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


def _to_kb_response(dto: KnowledgeBaseDTO) -> KnowledgeBaseResponse:
    return KnowledgeBaseResponse(**asdict(dto))


def _to_doc_response(dto: DocumentDTO) -> DocumentResponse:
    return DocumentResponse(**asdict(dto))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> KnowledgeBaseResponse:
    """创建知识库。"""
    dto = CreateKnowledgeBaseDTO(**request.model_dump())
    kb = await service.create_knowledge_base(dto, current_user.id)
    return _to_kb_response(kb)


@router.get("")
async def list_knowledge_bases(
    service: ServiceDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> KnowledgeBaseListResponse:
    """获取知识库列表。"""
    paged = await service.list_knowledge_bases(current_user.id, page=page, page_size=page_size)
    return KnowledgeBaseListResponse(
        items=[_to_kb_response(kb) for kb in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/{kb_id}")
async def get_knowledge_base(kb_id: int, service: ServiceDep, current_user: CurrentUserDep) -> KnowledgeBaseResponse:
    """获取知识库详情。"""
    kb = await service.get_knowledge_base(kb_id, current_user.id)
    return _to_kb_response(kb)


@router.put("/{kb_id}")
async def update_knowledge_base(
    kb_id: int,
    request: UpdateKnowledgeBaseRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> KnowledgeBaseResponse:
    """更新知识库。"""
    dto = UpdateKnowledgeBaseDTO(**request.model_dump())
    kb = await service.update_knowledge_base(kb_id, dto, current_user.id)
    return _to_kb_response(kb)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(kb_id: int, service: ServiceDep, current_user: CurrentUserDep) -> None:
    """删除知识库。"""
    await service.delete_knowledge_base(kb_id, current_user.id)


@router.post("/{kb_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: int,
    file: UploadFile,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> DocumentResponse:
    """上传文档。"""
    content = await file.read()
    dto = UploadDocumentDTO(
        filename=file.filename or "unnamed",
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
    doc = await service.upload_document(kb_id, dto, current_user.id)
    return _to_doc_response(doc)


@router.get("/{kb_id}/documents")
async def list_documents(
    kb_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DocumentListResponse:
    """获取文档列表。"""
    docs, total = await service.list_documents(kb_id, current_user.id, page=page, page_size=page_size)
    return DocumentListResponse(
        items=[_to_doc_response(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=calc_total_pages(total, page_size),
    )


@router.delete("/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(kb_id: int, doc_id: int, service: ServiceDep, current_user: CurrentUserDep) -> None:
    """删除文档。"""
    await service.delete_document(kb_id, doc_id, current_user.id)


@router.post("/{kb_id}/sync")
async def sync_knowledge_base(kb_id: int, service: ServiceDep, current_user: CurrentUserDep) -> KnowledgeBaseResponse:
    """手动触发知识库同步。"""
    kb = await service.sync_knowledge_base(kb_id, current_user.id)
    return _to_kb_response(kb)


@router.post("/{kb_id}/query")
async def query_knowledge_base(
    kb_id: int,
    request: QueryRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> QueryResponse:
    """RAG 检索。"""
    dto = QueryRequestDTO(query=request.query, top_k=request.top_k)
    result = await service.query(kb_id, dto, current_user.id)
    return QueryResponse(
        results=[
            QueryResultResponse(content=r.content, score=r.score, document_id=r.document_id, metadata=r.metadata)
            for r in result.results
        ],
        query=result.query,
        knowledge_base_id=result.knowledge_base_id,
    )
