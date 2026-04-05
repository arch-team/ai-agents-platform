"""Agents API 依赖注入。"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agents.application.services.agent_service import AgentService
from src.modules.agents.infrastructure.external.agentcore_runtime_manager import (
    AgentCoreRuntimeManager,
)
from src.modules.agents.infrastructure.external.workspace_manager import WorkspaceManagerImpl
from src.modules.agents.infrastructure.persistence.repositories.agent_blueprint_repository_impl import (
    AgentBlueprintRepositoryImpl,
)
from src.modules.agents.infrastructure.persistence.repositories.agent_repository_impl import (
    AgentRepositoryImpl,
)
from src.shared.infrastructure.database import get_db
from src.shared.infrastructure.settings import get_settings


async def get_agent_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AgentService:
    """创建 AgentService 实例 (CRUD 场景，无 Blueprint 依赖)。"""
    return AgentService(repository=AgentRepositoryImpl(session=session))


@lru_cache(maxsize=1)
def _get_runtime_manager() -> AgentCoreRuntimeManager:
    """创建 AgentCoreRuntimeManager 单例。"""
    import boto3

    settings = get_settings()
    client = boto3.client("bedrock-agent-runtime", region_name=settings.AWS_REGION)
    return AgentCoreRuntimeManager(
        client=client,
        ecr_repo_uri=settings.AGENTCORE_ECR_REPO_URI,
        env_name=settings.ENV_NAME,
    )


@lru_cache(maxsize=1)
def _get_workspace_manager() -> WorkspaceManagerImpl:
    """创建 WorkspaceManager 单例。"""
    from pathlib import Path

    settings = get_settings()
    return WorkspaceManagerImpl(
        workspace_root=Path(settings.WORKSPACE_ROOT),
        skill_library_root=Path(settings.SKILL_LIBRARY_ROOT),
        s3_bucket=settings.WORKSPACE_S3_BUCKET,
    )


async def get_lifecycle_agent_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AgentService:
    """创建 AgentService 实例 (Blueprint 生命周期场景，注入所有依赖)。"""
    return AgentService(
        repository=AgentRepositoryImpl(session=session),
        blueprint_repository=AgentBlueprintRepositoryImpl(session=session),
        workspace_manager=_get_workspace_manager(),
        runtime_manager=_get_runtime_manager(),
    )
