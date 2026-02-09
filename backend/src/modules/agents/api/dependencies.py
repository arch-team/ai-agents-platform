"""Agents API 依赖注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.infrastructure.persistence.repositories.agent_repository_impl import (
    AgentRepositoryImpl,
)
from src.shared.infrastructure.database import get_db


async def get_agent_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AgentService:
    """创建 AgentService 实例。"""
    return AgentService(repository=AgentRepositoryImpl(session=session))
