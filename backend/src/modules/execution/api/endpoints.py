"""Execution API 端点。"""

import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

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
)
from src.modules.execution.application.services.execution_service import ExecutionService
from src.shared.api.schemas import calc_total_pages
from src.shared.domain.exceptions import DomainError


router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

# 类型别名简化重复的依赖注入声明
ServiceDep = Annotated[ExecutionService, Depends(get_execution_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


def _to_conversation_response(dto: ConversationDTO) -> ConversationResponse:
    return ConversationResponse(
        id=dto.id,
        title=dto.title,
        agent_id=dto.agent_id,
        user_id=dto.user_id,
        status=dto.status,
        message_count=dto.message_count,
        total_tokens=dto.total_tokens,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


def _to_message_response(dto: MessageDTO) -> MessageResponse:
    return MessageResponse(
        id=dto.id,
        conversation_id=dto.conversation_id,
        role=dto.role,
        content=dto.content,
        token_count=dto.token_count,
        created_at=dto.created_at,
    )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ConversationResponse:
    """创建对话。"""
    dto = CreateConversationDTO(agent_id=request.agent_id, title=request.title)
    conversation = await service.create_conversation(dto, current_user.id)
    return _to_conversation_response(conversation)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    service: ServiceDep,
    current_user: CurrentUserDep,
    agent_id: Annotated[int | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ConversationListResponse:
    """获取当前用户的对话列表。"""
    paged = await service.list_conversations(
        user_id=current_user.id,
        agent_id=agent_id,
        page=page,
        page_size=page_size,
    )
    return ConversationListResponse(
        items=[_to_conversation_response(c) for c in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
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


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
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
) -> StreamingResponse:
    """SSE 流式发送消息。"""

    async def event_generator() -> AsyncIterator[str]:
        try:
            dto = SendMessageDTO(content=request.content)
            async for chunk in await service.send_message_stream(
                conversation_id,
                dto,
                current_user.id,
            ):
                yield chunk
        except DomainError as e:
            error_data = json.dumps({"error": e.message, "done": True})
            yield f"data: {error_data}\n\n"
        except Exception:
            error_data = json.dumps({"error": "服务内部错误", "done": True})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{conversation_id}/complete", response_model=ConversationResponse)
async def complete_conversation(
    conversation_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ConversationResponse:
    """结束对话。"""
    conversation = await service.complete_conversation(conversation_id, current_user.id)
    return _to_conversation_response(conversation)
