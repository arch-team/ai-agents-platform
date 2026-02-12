"""团队执行 API 端点。"""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.api.dependencies import get_team_execution_service
from src.modules.execution.api.schemas.team_requests import CreateTeamExecutionRequest
from src.modules.execution.api.schemas.team_responses import (
    TeamExecutionListResponse,
    TeamExecutionLogResponse,
    TeamExecutionResponse,
)
from src.modules.execution.application.dto.team_execution_dto import (
    CreateTeamExecutionDTO,
    TeamExecutionDTO,
)
from src.modules.execution.application.services.team_execution_service import (
    TeamExecutionService,
)
from src.shared.api.schemas import calc_total_pages


router = APIRouter(prefix="/api/v1/team-executions", tags=["team-executions"])

# 类型别名简化重复的依赖注入声明
ServiceDep = Annotated[TeamExecutionService, Depends(get_team_execution_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


def _to_response(dto: TeamExecutionDTO) -> TeamExecutionResponse:
    """将 DTO 转换为 API 响应模型。"""
    return TeamExecutionResponse(
        id=dto.id,
        agent_id=dto.agent_id,
        user_id=dto.user_id,
        conversation_id=dto.conversation_id,
        prompt=dto.prompt,
        status=dto.status,
        result=dto.result,
        error_message=dto.error_message,
        input_tokens=dto.input_tokens,
        output_tokens=dto.output_tokens,
        started_at=dto.started_at,
        completed_at=dto.completed_at,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.post(
    "",
    response_model=TeamExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_team_execution(
    request: CreateTeamExecutionRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> TeamExecutionResponse:
    """提交团队执行任务。"""
    dto = CreateTeamExecutionDTO(
        agent_id=request.agent_id,
        prompt=request.prompt,
        conversation_id=request.conversation_id,
    )
    result = await service.submit(dto, current_user.id)
    return _to_response(result)


@router.get("", response_model=TeamExecutionListResponse)
async def list_team_executions(
    service: ServiceDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TeamExecutionListResponse:
    """列出用户的团队执行任务。"""
    paged = await service.list_by_user(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return TeamExecutionListResponse(
        items=[_to_response(e) for e in paged.items],
        total=paged.total,
        page=page,
        page_size=page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/{execution_id}", response_model=TeamExecutionResponse)
async def get_team_execution(
    execution_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> TeamExecutionResponse:
    """获取团队执行详情。"""
    result = await service.get(execution_id, current_user.id)
    return _to_response(result)


@router.get(
    "/{execution_id}/logs",
    response_model=list[TeamExecutionLogResponse],
)
async def get_team_execution_logs(
    execution_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
    after_sequence: Annotated[int, Query(ge=0)] = 0,
) -> list[TeamExecutionLogResponse]:
    """获取执行日志（支持增量查询）。"""
    logs = await service.get_logs(execution_id, current_user.id, after_sequence)
    return [
        TeamExecutionLogResponse(
            id=log.id,
            execution_id=log.execution_id,
            sequence=log.sequence,
            log_type=log.log_type,
            content=log.content,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/{execution_id}/stream")
async def stream_team_execution_logs(
    execution_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> StreamingResponse:
    """SSE 进度推送。"""

    async def _event_generator() -> AsyncIterator[str]:
        """生成 SSE 事件流。"""
        try:
            async for log_dto in service.stream_logs(execution_id, current_user.id):
                data = json.dumps(
                    {
                        "id": log_dto.id,
                        "sequence": log_dto.sequence,
                        "log_type": log_dto.log_type,
                        "content": log_dto.content,
                    },
                    ensure_ascii=False,
                )
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{execution_id}/cancel", response_model=TeamExecutionResponse)
async def cancel_team_execution(
    execution_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> TeamExecutionResponse:
    """取消团队执行。"""
    result = await service.cancel(execution_id, current_user.id)
    return _to_response(result)
