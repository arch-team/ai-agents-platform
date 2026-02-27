"""Builder API 端点。"""

import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, status
from sse_starlette import EventSourceResponse, ServerSentEvent

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.builder.api.dependencies import get_builder_service
from src.modules.builder.api.schemas.requests import ConfirmBuilderRequest, TriggerBuilderRequest
from src.modules.builder.api.schemas.responses import BuilderSessionResponse
from src.modules.builder.application.dto.builder_dto import BuilderSessionDTO
from src.modules.builder.application.services.builder_service import BuilderService
from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/builder", tags=["builder"])

ServiceDep = Annotated[BuilderService, Depends(get_builder_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


def _to_response(dto: BuilderSessionDTO) -> BuilderSessionResponse:
    return BuilderSessionResponse(**asdict(dto))


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_builder_session(
    request: TriggerBuilderRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> BuilderSessionResponse:
    """创建 Builder 会话。"""
    from src.modules.builder.application.dto.builder_dto import TriggerBuilderDTO

    dto = TriggerBuilderDTO(prompt=request.prompt)
    result = await service.create_session(dto, current_user.id)
    return _to_response(result)


@router.post("/sessions/{session_id}/messages")
async def generate_config_stream(
    session_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> EventSourceResponse:
    """SSE 流式生成 Agent 配置 (受 SSEConnectionManager 并发限制)。"""
    from src.shared.infrastructure.sse_connection_manager import get_sse_manager

    sse_manager = get_sse_manager()

    async def event_generator() -> AsyncIterator[ServerSentEvent]:
        async with sse_manager.connect(current_user.id):
            try:
                async for chunk in service.generate_config_stream(session_id, current_user.id):
                    yield ServerSentEvent(data=json.dumps({"content": chunk, "done": False}))

                # 流结束后, 从已保存的会话中获取解析好的 config 发送给前端
                session_dto = await service.get_session(session_id, current_user.id)
                if session_dto.generated_config:
                    yield ServerSentEvent(data=json.dumps({"config": session_dto.generated_config, "done": False}))

                yield ServerSentEvent(data=json.dumps({"content": "", "done": True}))
            except DomainError as e:
                yield ServerSentEvent(data=json.dumps({"error": e.message, "done": True}))
            except Exception:
                logger.exception("builder_sse_stream_error", session_id=session_id)
                yield ServerSentEvent(data=json.dumps({"error": "服务内部错误", "done": True}))

    return EventSourceResponse(event_generator())


@router.post("/sessions/{session_id}/confirm")
async def confirm_builder_session(
    session_id: int,
    request: ConfirmBuilderRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> BuilderSessionResponse:
    """确认创建 Agent。"""
    result = await service.confirm_session(session_id, current_user.id, name_override=request.name_override)
    return _to_response(result)


@router.get("/sessions/{session_id}")
async def get_builder_session(
    session_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> BuilderSessionResponse:
    """查询 Builder 会话状态。"""
    result = await service.get_session(session_id, current_user.id)
    return _to_response(result)


@router.post("/sessions/{session_id}/cancel")
async def cancel_builder_session(
    session_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> BuilderSessionResponse:
    """取消 Builder 会话。"""
    result = await service.cancel_session(session_id, current_user.id)
    return _to_response(result)
