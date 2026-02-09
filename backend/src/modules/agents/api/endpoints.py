"""Agents API 端点。"""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.agents.api.dependencies import get_agent_service
from src.modules.agents.api.schemas.requests import CreateAgentRequest, UpdateAgentRequest
from src.modules.agents.api.schemas.responses import (
    AgentConfigResponse,
    AgentListResponse,
    AgentResponse,
)
from src.modules.agents.application.dto.agent_dto import AgentDTO, CreateAgentDTO, UpdateAgentDTO
from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO


router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


def _to_response(dto: AgentDTO) -> AgentResponse:
    """将 AgentDTO 转换为 API 响应模型。"""
    return AgentResponse(
        id=dto.id,
        name=dto.name,
        description=dto.description,
        system_prompt=dto.system_prompt,
        status=dto.status,
        owner_id=dto.owner_id,
        config=AgentConfigResponse(
            model_id=dto.model_id,
            temperature=dto.temperature,
            max_tokens=dto.max_tokens,
            top_p=dto.top_p,
        ),
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: CreateAgentRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> AgentResponse:
    """创建 Agent。"""
    dto = CreateAgentDTO(
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        model_id=request.model_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    agent = await service.create_agent(dto, current_user.id)
    return _to_response(agent)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[UserDTO, Depends(get_current_user)],
    status_filter: Annotated[AgentStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AgentListResponse:
    """获取当前用户的 Agent 列表。"""
    paged = await service.list_agents(
        owner_id=current_user.id,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(paged.total / page_size) if paged.total > 0 else 0
    return AgentListResponse(
        items=[_to_response(a) for a in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=total_pages,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    service: Annotated[AgentService, Depends(get_agent_service)],
    _current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> AgentResponse:
    """获取 Agent 详情。需要认证。"""
    agent = await service.get_agent(agent_id)
    return _to_response(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    request: UpdateAgentRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> AgentResponse:
    """更新 Agent。仅 owner 或 ADMIN 可操作。"""
    dto = UpdateAgentDTO(
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        model_id=request.model_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    agent = await service.update_agent(agent_id, dto, current_user.id)
    return _to_response(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> None:
    """删除 Agent。仅 DRAFT 状态可删除。"""
    await service.delete_agent(agent_id, current_user.id)


@router.post("/{agent_id}/activate", response_model=AgentResponse)
async def activate_agent(
    agent_id: int,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> AgentResponse:
    """激活 Agent。"""
    agent = await service.activate_agent(agent_id, current_user.id)
    return _to_response(agent)


@router.post("/{agent_id}/archive", response_model=AgentResponse)
async def archive_agent(
    agent_id: int,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> AgentResponse:
    """归档 Agent。"""
    agent = await service.archive_agent(agent_id, current_user.id)
    return _to_response(agent)
