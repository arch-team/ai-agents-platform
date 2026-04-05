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
from src.modules.skills.infrastructure.persistence.repositories.skill_repository_impl import (
    SkillRepositoryImpl,
)
from src.modules.skills.infrastructure.services.skill_querier_impl import SkillQuerierImpl
from src.modules.tool_catalog.infrastructure.persistence.repositories.tool_repository_impl import (
    ToolRepositoryImpl,
)
from src.modules.tool_catalog.infrastructure.services.tool_querier_impl import ToolQuerierImpl
from src.shared.domain.interfaces.agent_creator import IAgentCreator
from src.shared.domain.interfaces.agent_lifecycle import IAgentLifecycle
from src.shared.domain.interfaces.agent_querier import IAgentQuerier
from src.shared.domain.interfaces.knowledge_querier import IKnowledgeQuerier
from src.shared.domain.interfaces.skill_creator import ISkillCreator
from src.shared.domain.interfaces.skill_querier import ISkillQuerier
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


@lru_cache(maxsize=1)
def _get_workspace_manager() -> object:
    """创建 WorkspaceManagerImpl 单例。延迟导入避免循环依赖。"""
    import tempfile
    from pathlib import Path

    from src.modules.agents.infrastructure.external.workspace_manager import WorkspaceManagerImpl

    settings = get_settings()
    _tmp = Path(tempfile.gettempdir())
    return WorkspaceManagerImpl(
        workspace_root=Path(settings.WORKSPACE_ROOT) if settings.WORKSPACE_ROOT else _tmp / "agent-workspaces",
        skill_library_root=Path(settings.SKILL_LIBRARY_ROOT) if settings.SKILL_LIBRARY_ROOT else _tmp / "skill-library",
        s3_bucket=settings.WORKSPACE_S3_BUCKET,
    )


@lru_cache(maxsize=1)
def _get_runtime_manager() -> object:
    """创建 AgentCoreRuntimeManager 单例。延迟导入避免循环依赖。"""
    import boto3

    from src.modules.agents.infrastructure.external.agentcore_runtime_manager import AgentCoreRuntimeManager

    settings = get_settings()
    agentcore_client = boto3.client("bedrock-agentcore", region_name=settings.AWS_REGION)
    return AgentCoreRuntimeManager(
        client=agentcore_client,
        ecr_repo_uri=settings.AGENTCORE_ECR_REPO_URI,
        env_name=settings.ENV_NAME,
    )


async def get_agent_creator(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IAgentCreator:
    """创建 IAgentCreator 实例（供 builder 模块使用, V2 含 Blueprint + Workspace）。"""
    from src.modules.agents.infrastructure.persistence.repositories.agent_blueprint_repository_impl import (
        AgentBlueprintRepositoryImpl,
    )

    agent_repo = AgentRepositoryImpl(session=session)
    blueprint_repo = AgentBlueprintRepositoryImpl(session=session)
    workspace_mgr = _get_workspace_manager()
    runtime_mgr = _get_runtime_manager()

    agent_service = AgentService(
        repository=agent_repo,
        blueprint_repository=blueprint_repo,
        workspace_manager=workspace_mgr,  # type: ignore[arg-type]
        runtime_manager=runtime_mgr,  # type: ignore[arg-type]
    )
    return AgentCreatorImpl(
        agent_service=agent_service,
        agent_repository=agent_repo,
        blueprint_repository=blueprint_repo,
        workspace_manager=workspace_mgr,  # type: ignore[arg-type]
    )


async def get_agent_lifecycle(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IAgentLifecycle:
    """创建 IAgentLifecycle 实例（供 builder 模块使用）。

    复用 AgentCreatorImpl (同时实现 IAgentCreator + IAgentLifecycle)。
    """
    creator = await get_agent_creator(session)
    assert isinstance(creator, IAgentLifecycle)
    return creator


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


async def get_skill_querier(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ISkillQuerier:
    """创建 ISkillQuerier 实例（供 agents/builder 模块使用）。"""
    skill_repo = SkillRepositoryImpl(session=session)
    return SkillQuerierImpl(skill_repository=skill_repo)


async def get_skill_creator(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ISkillCreator:
    """创建 ISkillCreator 实例（供 builder 模块创建 Skill 使用）。延迟导入避免循环依赖。"""
    from pathlib import Path

    from src.modules.skills.application.services.skill_service import SkillService
    from src.modules.skills.infrastructure.external.skill_file_manager_impl import SkillFileManagerImpl
    from src.modules.skills.infrastructure.services.skill_creator_impl import SkillCreatorImpl

    settings = get_settings()
    skill_repo = SkillRepositoryImpl(session=session)
    file_manager = SkillFileManagerImpl(workspace_root=Path(settings.SKILL_LIBRARY_ROOT))
    skill_service = SkillService(repository=skill_repo, file_manager=file_manager)
    return SkillCreatorImpl(skill_service=skill_service)
