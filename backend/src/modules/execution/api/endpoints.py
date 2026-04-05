"""Execution API 端点。"""

from dataclasses import asdict
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, status
from sse_starlette import EventSourceResponse

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.api.dependencies import get_execution_service
from src.modules.execution.api.schemas.requests import CreateConversationRequest, SendMessageRequest
from src.modules.execution.api.schemas.responses import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from src.modules.execution.application.dto.execution_dto import (
    ConversationDTO,
    CreateConversationDTO,
    MessageDTO,
    SendMessageDTO,
    StreamChunk,
)
from src.modules.execution.application.services.execution_service import ExecutionService
from src.shared.api.schemas import calc_total_pages
from src.shared.infrastructure.sse_connection_manager import SSEConnectionManager, get_sse_manager


logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

ServiceDep = Annotated[ExecutionService, Depends(get_execution_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]
SSEManagerDep = Annotated[SSEConnectionManager, Depends(get_sse_manager)]


def _stream_chunk_to_dict(chunk: StreamChunk) -> dict[str, object]:
    """StreamChunk DTO 转换为 SSE data 字典，保持与前端约定的 JSON 格式。"""
    result: dict[str, object] = {"content": chunk.content, "done": chunk.done}
    if chunk.message_id is not None:
        result["message_id"] = chunk.message_id
    if chunk.token_count:
        result["token_count"] = chunk.token_count
    if chunk.error:
        result["error"] = chunk.error
    return result


def _to_conversation_response(dto: ConversationDTO) -> ConversationResponse:
    return ConversationResponse(**asdict(dto))


def _to_message_response(dto: MessageDTO) -> MessageResponse:
    return MessageResponse(**asdict(dto))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ConversationResponse:
    """创建对话。"""
    dto = CreateConversationDTO(agent_id=request.agent_id, title=request.title)
    conversation = await service.create_conversation(dto, current_user.id)
    return _to_conversation_response(conversation)


@router.get("")
async def list_conversations(
    service: ServiceDep,
    current_user: CurrentUserDep,
    agent_id: Annotated[int | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ConversationListResponse:
    """获取当前用户的对话列表。"""
    paged = await service.list_conversations(user_id=current_user.id, agent_id=agent_id, page=page, page_size=page_size)
    return ConversationListResponse(
        items=[_to_conversation_response(c) for c in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ConversationDetailResponse:
    """获取对话详情（含消息历史）。"""
    detail = await service.get_conversation(conversation_id, current_user.id)
    return ConversationDetailResponse(
        conversation=_to_conversation_response(detail.conversation),
        messages=[_to_message_response(m) for m in detail.messages],
    )


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: int,
    request: SendMessageRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    """发送消息（同步）。"""
    dto = SendMessageDTO(content=request.content)
    message = await service.send_message(conversation_id, dto, current_user.id)
    return _to_message_response(message)


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: int,
    request: SendMessageRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
    sse_manager: SSEManagerDep,
) -> EventSourceResponse:
    """SSE 流式发送消息。"""
    from src.shared.api.sse_helpers import stream_sse_events

    dto = SendMessageDTO(content=request.content)
    return EventSourceResponse(
        stream_sse_events(
            sse_manager,
            current_user.id,
            await service.send_message_stream(conversation_id, dto, current_user.id),
            format_chunk=_stream_chunk_to_dict,
            log_event="sse_stream_error",
            conversation_id=conversation_id,
        ),
    )


@router.post("/{conversation_id}/complete")
async def complete_conversation(
    conversation_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ConversationResponse:
    """结束对话。"""
    conversation = await service.complete_conversation(conversation_id, current_user.id)
    return _to_conversation_response(conversation)
