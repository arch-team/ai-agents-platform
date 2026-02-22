"""Builder API 依赖注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.builder.application.services.builder_service import BuilderService
from src.modules.builder.infrastructure.external.claude_builder_adapter import ClaudeBuilderAdapter
from src.modules.builder.infrastructure.persistence.repositories.builder_session_repository_impl import (
    BuilderSessionRepositoryImpl,
)
from src.presentation.api.providers import get_agent_creator
from src.shared.domain.interfaces.agent_creator import IAgentCreator
from src.shared.infrastructure.database import get_db


async def get_builder_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    agent_creator: Annotated[IAgentCreator, Depends(get_agent_creator)],
) -> BuilderService:
    """创建 BuilderService 实例。"""
    return BuilderService(
        session_repo=BuilderSessionRepositoryImpl(session=session),
        llm_service=ClaudeBuilderAdapter(),
        agent_creator=agent_creator,
    )
