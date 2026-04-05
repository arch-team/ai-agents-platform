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
from src.modules.builder.api.schemas.requests import ConfirmBuilderRequest, RefineBuilderRequest, TriggerBuilderRequest
from src.modules.builder.api.schemas.responses import (
    AvailableSkillResponse,
    AvailableToolResponse,
    BuilderSessionResponse,
)
from src.modules.builder.application.dto.builder_dto import BuilderSessionDTO, RefineBuilderDTO
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

    dto = TriggerBuilderDTO(
        prompt=request.prompt,
        template_id=request.template_id,
        selected_skill_ids=request.selected_skill_ids,
    )
    result = await service.create_session(dto, current_user.id)
    return _to_response(result)


@router.post("/sessions/{session_id}/generate")
async def generate_blueprint_stream(
    session_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> EventSourceResponse:
    """V2: SSE 流式生成 Agent Blueprint (SOP 引导式)。"""
    from src.shared.infrastructure.sse_connection_manager import get_sse_manager

    sse_manager = get_sse_manager()

    async def event_generator() -> AsyncIterator[ServerSentEvent]:
        async with sse_manager.connect(current_user.id):
            try:
                async for chunk in service.generate_blueprint_stream(session_id, current_user.id):
                    yield ServerSentEvent(data=json.dumps({"content": chunk, "done": False}))

                session_dto = await service.get_session(session_id, current_user.id)
                if session_dto.generated_blueprint:
                    yield ServerSentEvent(
                        data=json.dumps({"blueprint": session_dto.generated_blueprint, "done": False}),
                    )

                yield ServerSentEvent(data=json.dumps({"content": "", "done": True}))
            except DomainError as e:
                yield ServerSentEvent(data=json.dumps({"error": e.message, "done": True}))
            except Exception:
                logger.exception("builder_blueprint_stream_error", session_id=session_id)
                yield ServerSentEvent(data=json.dumps({"error": "服务内部错误", "done": True}))

    return EventSourceResponse(event_generator())


@router.post("/sessions/{session_id}/refine")
async def refine_builder_session(
    session_id: int,
    request: RefineBuilderRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> EventSourceResponse:
    """V2: 多轮迭代 — 用户追加需求后重新生成 Blueprint。"""
    from src.shared.infrastructure.sse_connection_manager import get_sse_manager

    sse_manager = get_sse_manager()
    dto = RefineBuilderDTO(message=request.message)

    async def event_generator() -> AsyncIterator[ServerSentEvent]:
        async with sse_manager.connect(current_user.id):
            try:
                async for chunk in service.refine_session(session_id, current_user.id, dto=dto):
                    yield ServerSentEvent(data=json.dumps({"content": chunk, "done": False}))

                session_dto = await service.get_session(session_id, current_user.id)
                if session_dto.generated_blueprint:
                    yield ServerSentEvent(
                        data=json.dumps({"blueprint": session_dto.generated_blueprint, "done": False}),
                    )

                yield ServerSentEvent(data=json.dumps({"content": "", "done": True}))
            except DomainError as e:
                yield ServerSentEvent(data=json.dumps({"error": e.message, "done": True}))
            except Exception:
                logger.exception("builder_refine_stream_error", session_id=session_id)
                yield ServerSentEvent(data=json.dumps({"error": "服务内部错误", "done": True}))

    return EventSourceResponse(event_generator())


@router.post("/sessions/{session_id}/confirm")
async def confirm_builder_session(
    session_id: int,
    request: ConfirmBuilderRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> BuilderSessionResponse:
    """确认创建 Agent (V1 JSON 配置 或 V2 Blueprint 均支持)。"""
    result = await service.confirm_session(
        session_id,
        current_user.id,
        name_override=request.name_override,
        auto_start_testing=request.auto_start_testing,
    )
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


@router.get("/available-tools")
async def list_available_tools(service: ServiceDep, current_user: CurrentUserDep) -> list[AvailableToolResponse]:
    """查询平台可用工具列表 (供前端展示和选择)。"""
    _ = current_user  # 认证校验
    tools = await service.get_available_tools()
    return [
        AvailableToolResponse(id=t.id, name=t.name, description=t.description, tool_type=t.tool_type) for t in tools
    ]


@router.get("/available-skills")
async def list_available_skills(service: ServiceDep, current_user: CurrentUserDep) -> list[AvailableSkillResponse]:
    """查询平台可用 Skill 列表 (供前端展示和选择)。"""
    _ = current_user  # 认证校验
    skills = await service.get_available_skills()
    return [
        AvailableSkillResponse(id=s.id, name=s.name, description=s.description, category=s.category) for s in skills
    ]
