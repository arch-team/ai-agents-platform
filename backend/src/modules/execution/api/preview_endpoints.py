"""Agent 预览端点 — 单轮测试，不创建 Conversation，不持久化消息。"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.api.dependencies import get_agent_runtime
from src.modules.execution.application.interfaces.agent_runtime import (
    AgentRequest,
    IAgentRuntime,
)
from src.modules.execution.domain.exceptions import AgentNotAvailableError
from src.presentation.api.providers import get_agent_querier
from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo, IAgentQuerier


router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


class PreviewAgentRequest(BaseModel):
    """Agent 预览请求。"""

    prompt: str = Field(..., min_length=1, max_length=2000)


class AgentPreviewResponse(BaseModel):
    """Agent 预览响应。"""

    content: str
    model_id: str
    tokens_input: int
    tokens_output: int


@router.post("/{agent_id}/preview")
async def preview_agent(
    agent_id: int,
    request: PreviewAgentRequest,
    current_user: CurrentUserDep,
    agent_runtime: Annotated[IAgentRuntime, Depends(get_agent_runtime)],
    agent_querier: Annotated[IAgentQuerier, Depends(get_agent_querier)],
) -> AgentPreviewResponse:
    """预览 Agent — 单轮测试，不创建 Conversation，不持久化消息。"""
    agent_info: ActiveAgentInfo | None = await agent_querier.get_active_agent(agent_id)
    if agent_info is None:
        raise AgentNotAvailableError(agent_id)

    agent_request = AgentRequest(
        prompt=request.prompt,
        system_prompt=agent_info.system_prompt,
        model_id=agent_info.model_id,
        temperature=agent_info.temperature,
        max_tokens=agent_info.max_tokens,
        max_turns=1,
    )
    chunk = await agent_runtime.execute(agent_request)

    return AgentPreviewResponse(
        content=chunk.content,
        model_id=agent_info.model_id,
        tokens_input=chunk.input_tokens,
        tokens_output=chunk.output_tokens,
    )
