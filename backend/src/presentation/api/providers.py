"""跨模块依赖提供者。

composition root 层的工厂函数，负责跨模块对象的组装。
各模块 API 层的 dependencies.py 从此处导入，
避免模块间直接依赖，遵循架构隔离规则。
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agents.infrastructure.persistence.repositories.agent_repository_impl import (
    AgentRepositoryImpl,
)
from src.modules.agents.infrastructure.services.agent_querier_impl import AgentQuerierImpl
from src.shared.domain.interfaces.agent_querier import IAgentQuerier
from src.shared.infrastructure.database import get_db


async def get_agent_querier(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IAgentQuerier:
    """创建 IAgentQuerier 实例。"""
    agent_repo = AgentRepositoryImpl(session=session)
    return AgentQuerierImpl(agent_repository=agent_repo)
