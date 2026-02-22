"""IAgentCreator 的具体实现，用于 builder 模块的跨模块创建调用。"""

from src.modules.agents.application.dto.agent_dto import CreateAgentDTO
from src.modules.agents.application.services.agent_service import AgentService
from src.shared.domain.interfaces.agent_creator import (
    CreateAgentRequest,
    CreatedAgentInfo,
    IAgentCreator,
)


class AgentCreatorImpl(IAgentCreator):
    """通过 AgentService 实现 IAgentCreator 接口。"""

    def __init__(self, agent_service: AgentService) -> None:
        self._agent_service = agent_service

    async def create_agent(self, request: CreateAgentRequest, owner_id: int) -> CreatedAgentInfo:
        """调用 AgentService 创建 Agent 并返回跨模块 DTO。"""
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
