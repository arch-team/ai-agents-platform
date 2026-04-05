"""Memory API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.api.dependencies import get_memory_service
from src.modules.execution.api.schemas.memory_schemas import (
    MemoryItemResponse,
    SaveMemoryRequest,
    SaveMemoryResponse,
    SearchMemoryRequest,
)
from src.modules.execution.application.interfaces import IMemoryService, MemoryItem
from src.modules.execution.domain.exceptions import MemoryNotEnabledError
from src.presentation.api.providers import get_agent_querier
from src.shared.domain.interfaces.agent_querier import IAgentQuerier


router = APIRouter(prefix="/api/v1/agents/{agent_id}/memories", tags=["memories"])

MemoryServiceDep = Annotated[IMemoryService, Depends(get_memory_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]
AgentQuerierDep = Annotated[IAgentQuerier, Depends(get_agent_querier)]


def _to_response(item: MemoryItem) -> MemoryItemResponse:
    return MemoryItemResponse(
        memory_id=item.memory_id,
        content=item.content,
        topic=item.topic,
        relevance_score=item.relevance_score,
    )


async def _check_memory_enabled(agent_id: int, agent_querier: IAgentQuerier) -> None:
    """校验 Agent 存在且已启用 Memory。"""
    info = await agent_querier.get_executable_agent(agent_id)
    if info is None or not info.enable_memory:
        raise MemoryNotEnabledError(agent_id)


@router.get("")
async def list_memories(
    agent_id: int,
    memory_service: MemoryServiceDep,
    _current_user: CurrentUserDep,  # auth guard
    agent_querier: AgentQuerierDep,
    max_results: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[MemoryItemResponse]:
    """列出 Agent 的长期记忆。"""
    await _check_memory_enabled(agent_id, agent_querier)
    items = await memory_service.list_memories(agent_id, max_results=max_results)
    return [_to_response(item) for item in items]


@router.post("", status_code=status.HTTP_201_CREATED)
async def save_memory(
    agent_id: int,
    request: SaveMemoryRequest,
    memory_service: MemoryServiceDep,
    _current_user: CurrentUserDep,  # auth guard
    agent_querier: AgentQuerierDep,
) -> SaveMemoryResponse:
    """保存一条记忆到 Agent 的 Memory。"""
    await _check_memory_enabled(agent_id, agent_querier)
    memory_id = await memory_service.save_memory(agent_id, request.content, request.topic)
    return SaveMemoryResponse(memory_id=memory_id)


@router.post("/search")
async def search_memories(
    agent_id: int,
    request: SearchMemoryRequest,
    memory_service: MemoryServiceDep,
    _current_user: CurrentUserDep,  # auth guard
    agent_querier: AgentQuerierDep,
) -> list[MemoryItemResponse]:
    """语义搜索 Agent 记忆。"""
    await _check_memory_enabled(agent_id, agent_querier)
    items = await memory_service.recall_memory(agent_id, request.query, max_results=request.max_results)
    return [_to_response(item) for item in items]


@router.get("/{memory_id}")
async def get_memory(
    agent_id: int,
    memory_id: str,
    memory_service: MemoryServiceDep,
    _current_user: CurrentUserDep,  # auth guard
    agent_querier: AgentQuerierDep,
) -> MemoryItemResponse:
    """获取单条记忆。"""
    await _check_memory_enabled(agent_id, agent_querier)
    item = await memory_service.get_memory(agent_id, memory_id)
    if item is None:
        from src.shared.domain.exceptions import EntityNotFoundError

        raise EntityNotFoundError(entity_type="Memory", entity_id=memory_id)
    return _to_response(item)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    agent_id: int,
    memory_id: str,
    memory_service: MemoryServiceDep,
    _current_user: CurrentUserDep,  # auth guard
    agent_querier: AgentQuerierDep,
) -> None:
    """删除单条记忆。"""
    await _check_memory_enabled(agent_id, agent_querier)
    await memory_service.delete_memory(agent_id, memory_id)
