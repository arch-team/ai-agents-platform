"""Agents API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.agents.api.dependencies import (
    get_agent_service,
    get_lifecycle_agent_service,
)
from src.modules.agents.api.schemas.requests import CreateAgentRequest, UpdateAgentRequest
from src.modules.agents.api.schemas.responses import (
    AgentConfigResponse,
    AgentListResponse,
    AgentResponse,
)
from src.modules.agents.application.dto.agent_dto import AgentDTO, UpdateAgentDTO
from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.modules.auth.api.dependencies import get_current_user, require_role
from src.modules.auth.application.dto.user_dto import UserDTO
from src.presentation.api.providers import get_agent_creator
from src.shared.api.schemas import calc_total_pages
from src.shared.domain.interfaces.agent_creator import (
    BlueprintData,
    CreateAgentWithBlueprintRequest,
    IAgentCreator,
    PersonaData,
    ToolBindingData,
)
from src.shared.domain.value_objects.role import Role


router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

ServiceDep = Annotated[AgentService, Depends(get_agent_service)]
AgentCreatorDep = Annotated[IAgentCreator, Depends(get_agent_creator)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


def _to_response(dto: AgentDTO) -> AgentResponse:
    """AgentDTO -> AgentResponse（含嵌套 config 结构）。"""
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
            runtime_type=dto.runtime_type,
            enable_teams=dto.enable_teams,
            enable_memory=dto.enable_memory,
            tool_ids=dto.tool_ids,
        ),
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: CreateAgentRequest,
    agent_creator: AgentCreatorDep,
    service: ServiceDep,
    current_user: Annotated[UserDTO, Depends(require_role(Role.DEVELOPER, Role.ADMIN))],
) -> AgentResponse:
    """创建 Agent (自动创建最小 Blueprint)。仅 DEVELOPER 和 ADMIN 可创建。"""
    blueprint = BlueprintData(
        persona=PersonaData(
            role=request.persona_role or request.name,
            background=request.persona_background or request.description,
            tone=request.persona_tone,
        ),
        tool_bindings=tuple(ToolBindingData(tool_id=tid, display_name="") for tid in request.tool_ids),
        memory_enabled=request.enable_memory,
    )
    cmd = CreateAgentWithBlueprintRequest(
        name=request.name,
        blueprint=blueprint,
        description=request.description,
        model_id=request.model_id,
    )
    result = await agent_creator.create_agent_with_blueprint(cmd, current_user.id)
    agent = await service.get_owned_agent(result.id, current_user.id)
    return _to_response(agent)


@router.get("")
async def list_agents(
    service: ServiceDep,
    current_user: CurrentUserDep,
    status_filter: Annotated[AgentStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AgentListResponse:
    """获取当前用户的 Agent 列表。"""
    paged = await service.list_agents(owner_id=current_user.id, status=status_filter, page=page, page_size=page_size)
    return AgentListResponse(
        items=[_to_response(a) for a in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, page_size),
    )


@router.get("/{agent_id}")
async def get_agent(agent_id: int, service: ServiceDep, current_user: CurrentUserDep) -> AgentResponse:
    """获取 Agent 详情。校验所有权，防止越权访问。"""
    agent = await service.get_owned_agent(agent_id, current_user.id)
    return _to_response(agent)


@router.put("/{agent_id}")
async def update_agent(
    agent_id: int,
    request: UpdateAgentRequest,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> AgentResponse:
    """更新 Agent。"""
    dto = UpdateAgentDTO(**request.model_dump())
    agent = await service.update_agent(agent_id, dto, current_user.id)
    return _to_response(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: int, service: ServiceDep, current_user: CurrentUserDep) -> None:
    """删除 Agent。仅 DRAFT 状态可删除。"""
    await service.delete_agent(agent_id, current_user.id)


@router.post("/{agent_id}/activate")
async def activate_agent(agent_id: int, service: ServiceDep, current_user: CurrentUserDep) -> AgentResponse:
    """激活 Agent。"""
    agent = await service.activate_agent(agent_id, current_user.id)
    return _to_response(agent)


@router.post("/{agent_id}/archive")
async def archive_agent(agent_id: int, service: ServiceDep, current_user: CurrentUserDep) -> AgentResponse:
    """归档 Agent。"""
    agent = await service.archive_agent(agent_id, current_user.id)
    return _to_response(agent)


# ── Blueprint 生命周期端点 ──


LifecycleServiceDep = Annotated[AgentService, Depends(get_lifecycle_agent_service)]


@router.post("/{agent_id}/start-testing")
async def start_testing(agent_id: int, service: LifecycleServiceDep, current_user: CurrentUserDep) -> AgentResponse:
    """开始测试: DRAFT → TESTING。创建专属 Runtime。"""
    agent = await service.start_testing(agent_id, current_user.id)
    return _to_response(agent)


@router.post("/{agent_id}/go-live")
async def go_live(agent_id: int, service: LifecycleServiceDep, current_user: CurrentUserDep) -> AgentResponse:
    """上线发布: TESTING → ACTIVE。复用同一 Runtime。"""
    agent = await service.go_live(agent_id, current_user.id)
    return _to_response(agent)


@router.post("/{agent_id}/take-offline")
async def take_offline(agent_id: int, service: LifecycleServiceDep, current_user: CurrentUserDep) -> AgentResponse:
    """下线归档: ACTIVE → ARCHIVED。销毁 Runtime。"""
    agent = await service.take_offline(agent_id, current_user.id)
    return _to_response(agent)


# ── Blueprint 详情端点 ──

from src.modules.agents.api.dependencies import get_blueprint_repository  # noqa: E402
from src.modules.agents.api.schemas.responses import (  # noqa: E402
    BlueprintDetailResponse,
    BlueprintGuardrailResponse,
    BlueprintPersonaResponse,
    BlueprintToolBindingResponse,
)
from src.modules.agents.domain.repositories.agent_blueprint_repository import (  # noqa: E402
    IAgentBlueprintRepository,
)


BlueprintRepoDep = Annotated[IAgentBlueprintRepository, Depends(get_blueprint_repository)]


@router.get("/{agent_id}/blueprint")
async def get_blueprint(
    agent_id: int,
    service: ServiceDep,
    current_user: CurrentUserDep,
    blueprint_repo: BlueprintRepoDep,
) -> BlueprintDetailResponse:
    """获取 Agent 的 Blueprint 完整配置信息。"""
    from src.shared.domain.exceptions import EntityNotFoundError

    # 校验所有权
    await service.get_owned_agent(agent_id, current_user.id)

    detail = await blueprint_repo.get_blueprint_detail(agent_id)
    if detail is None:
        entity_name = "Blueprint"
        raise EntityNotFoundError(entity_type=entity_name, entity_id=agent_id)

    persona_data = detail.persona or {}
    return BlueprintDetailResponse(
        persona=BlueprintPersonaResponse(
            role=persona_data.get("role", ""),
            background=persona_data.get("background", ""),
            tone=persona_data.get("tone", ""),
        ),
        guardrails=[
            BlueprintGuardrailResponse(rule=g.get("rule", ""), severity=g.get("severity", "warn"))
            for g in detail.guardrails
        ],
        memory_config=detail.memory_config,
        knowledge_base_ids=detail.knowledge_base_ids,
        skill_ids=detail.skill_ids,
        tool_bindings=[
            BlueprintToolBindingResponse(tool_id=tb.tool_id, display_name=tb.display_name, usage_hint=tb.usage_hint)
            for tb in detail.tool_bindings
        ],
    )
