"""团队执行 API 端点。"""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, status
from sse_starlette import EventSourceResponse, ServerSentEvent

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.api.dependencies import get_team_execution_service
from src.modules.execution.api.schemas.team_requests import CreateTeamExecutionRequest
from src.modules.execution.api.schemas.team_responses import (
    TeamExecutionListResponse,
    TeamExecutionLogResponse,
    TeamExecutionResponse,
)
from src.modules.execution.application.dto.team_execution_dto import CreateTeamExecutionDTO, TeamExecutionDTO
from src.modules.execution.application.services.team_execution_service import TeamExecutionService
from src.shared.api.schemas import calc_total_pages
from src.shared.infrastructure.sse_connection_manager import SSEConnectionManager, get_sse_manager


logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/team-executions", tags=["team-executions"])

ServiceDep = Annotated[TeamExecutionService, Depends(get_team_execution_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]
SSEManagerDep = Annotated[SSEConnectionManager, Depends(get_sse_manager)]


def _to_response(dto: TeamExecutionDTO) -> TeamExecutionResponse:
    return TeamExecutionResponse(**asdict(dto))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_team_execution(
    request: CreateTeamExecutionRequest, service: ServiceDep, current_user: CurrentUserDep,
) -> TeamExecutionResponse:
    """提交团队执行任务。"""
    dto = CreateTeamExecutionDTO(**request.model_dump())
    result = await service.submit(dto, current_user.id)
    return _to_response(result)


@router.get("")
async def list_team_executions(
    service: ServiceDep, current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TeamExecutionListResponse:
    """列出用户的团队执行任务。"""
    paged = await service.list_by_user(user_id=current_user.id, page=page, page_size=page_size)
    return TeamExecutionListResponse(
        items=[_to_response(e) for e in paged.items],
        total=paged.total, page=page, page_size=page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/{execution_id}")
async def get_team_execution(
    execution_id: int, service: ServiceDep, current_user: CurrentUserDep,
) -> TeamExecutionResponse:
    """获取团队执行详情。"""
    result = await service.get(execution_id, current_user.id)
    return _to_response(result)


@router.get("/{execution_id}/logs")
async def get_team_execution_logs(
    execution_id: int, service: ServiceDep, current_user: CurrentUserDep,
    after_sequence: Annotated[int, Query(ge=0)] = 0,
) -> list[TeamExecutionLogResponse]:
    """获取执行日志（支持增量查询）。"""
    logs = await service.get_logs(execution_id, current_user.id, after_sequence)
    return [
        TeamExecutionLogResponse(
            id=log.id, execution_id=log.execution_id, sequence=log.sequence,
            log_type=log.log_type, content=log.content, created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/{execution_id}/stream")
async def stream_team_execution_logs(
    execution_id: int, service: ServiceDep, current_user: CurrentUserDep, sse_manager: SSEManagerDep,
) -> EventSourceResponse:
    """SSE 进度推送。"""

    async def _event_generator() -> AsyncIterator[ServerSentEvent]:
        async with sse_manager.connect(current_user.id):
            try:
                async for log_dto in service.stream_logs(execution_id, current_user.id):
                    data = json.dumps(
                        {"id": log_dto.id, "sequence": log_dto.sequence,
                         "log_type": log_dto.log_type, "content": log_dto.content},
                        ensure_ascii=False,
                    )
                    yield ServerSentEvent(data=data)
                yield ServerSentEvent(data="[DONE]")
            except asyncio.CancelledError:
                return
            except Exception:
                logger.exception("sse_stream_error", execution_id=execution_id)
                error_data = json.dumps({"error": "服务内部错误", "done": True}, ensure_ascii=False)
                yield ServerSentEvent(data=error_data)

    return EventSourceResponse(_event_generator())


@router.post("/{execution_id}/cancel")
async def cancel_team_execution(
    execution_id: int, service: ServiceDep, current_user: CurrentUserDep,
) -> TeamExecutionResponse:
    """取消团队执行。"""
    result = await service.cancel(execution_id, current_user.id)
    return _to_response(result)
