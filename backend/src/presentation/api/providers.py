"""跨模块依赖提供者。

composition root 层的工厂函数，负责跨模块对象的组装。
各模块 API 层的 dependencies.py 从此处导入，
避免模块间直接依赖，遵循架构隔离规则。
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.infrastructure.persistence.repositories.agent_repository_impl import (
    AgentRepositoryImpl,
)
from src.modules.agents.infrastructure.services.agent_creator_impl import AgentCreatorImpl
from src.modules.agents.infrastructure.services.agent_querier_impl import AgentQuerierImpl
from src.modules.knowledge.api.dependencies import get_bedrock_knowledge_client
from src.modules.knowledge.infrastructure.persistence.repositories.knowledge_base_repository_impl import (
    KnowledgeBaseRepositoryImpl,
)
from src.modules.knowledge.infrastructure.services.knowledge_querier_impl import KnowledgeQuerierImpl
from src.modules.tool_catalog.infrastructure.persistence.repositories.tool_repository_impl import (
    ToolRepositoryImpl,
)
from src.modules.tool_catalog.infrastructure.services.tool_querier_impl import ToolQuerierImpl
from src.shared.domain.interfaces.agent_creator import IAgentCreator
from src.shared.domain.interfaces.agent_querier import IAgentQuerier
from src.shared.domain.interfaces.knowledge_querier import IKnowledgeQuerier
from src.shared.domain.interfaces.tool_querier import IToolQuerier
from src.shared.infrastructure.database import get_db
from src.shared.infrastructure.settings import get_settings


@lru_cache(maxsize=1)
def get_gateway_sync() -> object:
    """创建 GatewaySyncAdapter 单例。延迟导入避免循环依赖。

    返回类型为 GatewaySyncAdapter (实现 IGatewaySyncService Protocol)，
    声明为 object 以避免循环导入。
    """
    from src.modules.tool_catalog.infrastructure.external.gateway_sync_adapter import GatewaySyncAdapter

    settings = get_settings()
    return GatewaySyncAdapter(
        gateway_id=settings.AGENTCORE_GATEWAY_ID,
        region=settings.AWS_REGION,
    )


async def get_agent_querier(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IAgentQuerier:
    """创建 IAgentQuerier 实例。"""
    agent_repo = AgentRepositoryImpl(session=session)
    return AgentQuerierImpl(agent_repository=agent_repo)


async def get_agent_creator(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IAgentCreator:
    """创建 IAgentCreator 实例（供 builder 模块使用）。"""
    agent_repo = AgentRepositoryImpl(session=session)
    agent_service = AgentService(repository=agent_repo)
    return AgentCreatorImpl(agent_service=agent_service)


async def get_tool_querier(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IToolQuerier:
    """创建 IToolQuerier 实例，注入 AgentQuerier 实现 Agent 级别工具过滤。"""
    tool_repo = ToolRepositoryImpl(session=session)
    agent_repo = AgentRepositoryImpl(session=session)
    agent_querier = AgentQuerierImpl(agent_repository=agent_repo)
    return ToolQuerierImpl(tool_repository=tool_repo, agent_querier=agent_querier)


async def get_knowledge_querier(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IKnowledgeQuerier:
    """创建 IKnowledgeQuerier 实例。"""
    kb_repo = KnowledgeBaseRepositoryImpl(session=session)
    knowledge_svc = get_bedrock_knowledge_client()
    return KnowledgeQuerierImpl(kb_repository=kb_repo, knowledge_service=knowledge_svc)
