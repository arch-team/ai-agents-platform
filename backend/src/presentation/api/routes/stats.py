"""Dashboard 统计端点。"""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.modules.agents.infrastructure.persistence.repositories.agent_repository_impl import (
    AgentRepositoryImpl,
)
from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.domain.repositories.conversation_repository import IConversationRepository
from src.modules.execution.domain.repositories.team_execution_repository import ITeamExecutionRepository
from src.modules.execution.infrastructure.persistence.repositories.conversation_repository_impl import (
    ConversationRepositoryImpl,
)
from src.modules.execution.infrastructure.persistence.repositories.team_execution_repository_impl import (
    TeamExecutionRepositoryImpl,
)
from src.shared.infrastructure.database import get_db


router = APIRouter(prefix="/api/v1/stats", tags=["stats"])

CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


class DashboardSummaryResponse(BaseModel):
    """Dashboard 统计摘要响应。"""

    agents_total: int
    conversations_total: int
    team_executions_total: int


def _get_repos(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> tuple[IAgentRepository, IConversationRepository, ITeamExecutionRepository]:
    """创建统计查询所需的 Repository 实例。"""
    return (
        AgentRepositoryImpl(session=db),
        ConversationRepositoryImpl(session=db),
        TeamExecutionRepositoryImpl(session=db),
    )


ReposDep = Annotated[
    tuple[IAgentRepository, IConversationRepository, ITeamExecutionRepository],
    Depends(_get_repos),
]


@router.get("/summary")
async def get_summary(current_user: CurrentUserDep, repos: ReposDep) -> DashboardSummaryResponse:
    """获取 Dashboard 统计摘要。

    ADMIN 角色可查看全部数据，普通用户只能查看自己的数据。
    """
    agent_repo, conversation_repo, team_execution_repo = repos
    is_admin = current_user.role == "admin"

    if is_admin:
        agents_total, conversations_total, team_executions_total = await asyncio.gather(
            agent_repo.count(),
            conversation_repo.count(),
            team_execution_repo.count(),
        )
    else:
        agents_total, conversations_total, team_executions_total = await asyncio.gather(
            agent_repo.count_by_owner(current_user.id),
            conversation_repo.count_by_user(current_user.id),
            team_execution_repo.count_by_user(current_user.id),
        )

    return DashboardSummaryResponse(
        agents_total=agents_total,
        conversations_total=conversations_total,
        team_executions_total=team_executions_total,
    )
