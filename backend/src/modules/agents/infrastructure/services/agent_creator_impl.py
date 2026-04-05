"""IAgentCreator 的具体实现，用于 builder 模块的跨模块创建调用。"""

import json

import structlog

from src.modules.agents.application.dto.agent_dto import CreateAgentDTO
from src.modules.agents.application.interfaces.workspace_manager import (
    BlueprintDTO,
    GuardrailDTO,
    IWorkspaceManager,
    ToolBindingDTO,
)
from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.domain.repositories.agent_blueprint_repository import (
    CreateBlueprintDTO,
    CreateToolBindingDTO,
    IAgentBlueprintRepository,
)
from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.shared.domain.interfaces.agent_creator import (
    CreateAgentRequest,
    CreateAgentWithBlueprintRequest,
    CreatedAgentInfo,
    IAgentCreator,
)


log = structlog.get_logger(__name__)


class AgentCreatorImpl(IAgentCreator):
    """通过 AgentService 实现 IAgentCreator 接口。"""

    def __init__(
        self,
        agent_service: AgentService,
        agent_repository: IAgentRepository | None = None,
        blueprint_repository: IAgentBlueprintRepository | None = None,
        workspace_manager: IWorkspaceManager | None = None,
    ) -> None:
        self._agent_service = agent_service
        self._agent_repo = agent_repository
        self._blueprint_repo = blueprint_repository
        self._workspace_manager = workspace_manager

    async def create_agent(self, request: CreateAgentRequest, owner_id: int) -> CreatedAgentInfo:
        """V1: 调用 AgentService 创建简单 Agent。"""
        dto = CreateAgentDTO(
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            model_id=request.model_id or "",
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        agent_dto = await self._agent_service.create_agent(dto=dto, owner_id=owner_id)
        return CreatedAgentInfo(id=agent_dto.id, name=agent_dto.name, status=agent_dto.status)

    async def create_agent_with_blueprint(
        self,
        request: CreateAgentWithBlueprintRequest,
        owner_id: int,
    ) -> CreatedAgentInfo:
        """V2: 创建 Agent + Blueprint 记录 + 工作目录。

        编排流程:
        1. 创建 Agent (DRAFT)
        2. 创建 Blueprint DB 记录 (关联 skills + tool_bindings)
        3. 设置 Agent.blueprint_id
        4. 创建 workspace 目录
        5. 更新 Blueprint.workspace_path
        """
        bp = request.blueprint

        if self._blueprint_repo is None or self._workspace_manager is None or self._agent_repo is None:
            return await super().create_agent_with_blueprint(request, owner_id)

        # 1. 创建 Agent (DRAFT)
        system_prompt = f"你是{bp.persona.role}。{bp.persona.background}"
        agent_info = await self.create_agent(
            CreateAgentRequest(
                name=request.name,
                system_prompt=system_prompt,
                description=request.description,
                model_id=request.model_id,
            ),
            owner_id,
        )

        # 2. 创建 Blueprint DB 记录
        persona_json = json.dumps(
            {"role": bp.persona.role, "background": bp.persona.background, "tone": bp.persona.tone},
            ensure_ascii=False,
        )
        guardrails_json = json.dumps(
            [{"rule": g.rule, "severity": g.severity} for g in bp.guardrails],
            ensure_ascii=False,
        )
        blueprint_id = await self._blueprint_repo.create_blueprint(
            CreateBlueprintDTO(
                agent_id=agent_info.id,
                persona_config=persona_json,
                guardrails=guardrails_json,
                knowledge_base_ids=json.dumps(request.knowledge_base_ids),
                skill_ids=list(bp.skill_ids),
                tool_bindings=[
                    CreateToolBindingDTO(tool_id=tb.tool_id, display_name=tb.display_name, usage_hint=tb.usage_hint)
                    for tb in bp.tool_bindings
                ],
            ),
        )

        # 3. 设置 Agent.blueprint_id (直接仓储操作, 避免走完整 update 流程)
        agent = await self._agent_repo.get_by_id(agent_info.id)
        if agent is not None:
            agent.blueprint_id = blueprint_id
            agent.touch()
            await self._agent_repo.update(agent)

        # 4. 创建 workspace 目录
        workspace_blueprint = BlueprintDTO(
            agent_name=request.name,
            persona_role=bp.persona.role,
            persona_background=bp.persona.background,
            persona_tone=bp.persona.tone,
            guardrails=tuple(GuardrailDTO(rule=g.rule, severity=g.severity) for g in bp.guardrails),
            memory_enabled=bp.memory_enabled,
            memory_retain_fields=bp.memory_retain_fields,
            skill_paths=bp.skill_paths,
            tool_bindings=tuple(
                ToolBindingDTO(display_name=tb.display_name, usage_hint=tb.usage_hint) for tb in bp.tool_bindings
            ),
        )
        workspace_path = await self._workspace_manager.create_workspace(agent_info.id, workspace_blueprint)

        # 5. 更新 Blueprint.workspace_path
        await self._blueprint_repo.update_workspace_path(agent_info.id, str(workspace_path))

        log.info(
            "agent_created_with_blueprint",
            agent_id=agent_info.id,
            blueprint_id=blueprint_id,
            workspace_path=str(workspace_path),
        )
        return agent_info

    async def start_testing(self, agent_id: int, operator_id: int) -> CreatedAgentInfo:
        """触发 DRAFT → TESTING: S3 上传 + Runtime 创建。"""
        agent_dto = await self._agent_service.start_testing(agent_id, operator_id)
        return CreatedAgentInfo(id=agent_dto.id, name=agent_dto.name, status=agent_dto.status)
