"""Builder API 依赖注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.builder.application.services.builder_service import BuilderService
from src.modules.builder.infrastructure.external.claude_builder_adapter import ClaudeBuilderAdapter
from src.modules.builder.infrastructure.persistence.repositories.builder_session_repository_impl import (
    BuilderSessionRepositoryImpl,
)
from src.presentation.api.providers import get_agent_creator, get_skill_creator, get_skill_querier, get_tool_querier
from src.shared.domain.interfaces.agent_creator import IAgentCreator
from src.shared.domain.interfaces.skill_creator import ISkillCreator
from src.shared.domain.interfaces.skill_querier import ISkillQuerier
from src.shared.domain.interfaces.tool_querier import IToolQuerier
from src.shared.infrastructure.database import get_db


async def get_builder_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    agent_creator: Annotated[IAgentCreator, Depends(get_agent_creator)],
    skill_creator: Annotated[ISkillCreator, Depends(get_skill_creator)],
    tool_querier: Annotated[IToolQuerier, Depends(get_tool_querier)],
    skill_querier: Annotated[ISkillQuerier, Depends(get_skill_querier)],
) -> BuilderService:
    """创建 BuilderService 实例 (V2: 注入全部跨模块依赖)。"""
    return BuilderService(
        session_repo=BuilderSessionRepositoryImpl(session=session),
        llm_service=ClaudeBuilderAdapter(),
        agent_creator=agent_creator,
        skill_creator=skill_creator,
        tool_querier=tool_querier,
        skill_querier=skill_querier,
    )
