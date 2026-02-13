"""Dashboard 统计端点。"""

from __future__ import annotations

import asyncio
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agents.infrastructure.persistence.models.agent_model import AgentModel
from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.infrastructure.persistence.models.conversation_model import ConversationModel
from src.modules.execution.infrastructure.persistence.models.team_execution_model import TeamExecutionModel
from src.shared.infrastructure.database import get_db


router = APIRouter(prefix="/api/v1/stats", tags=["stats"])
logger = structlog.get_logger(__name__)

CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]
SessionDep = Annotated[AsyncSession, Depends(get_db)]


class DashboardSummaryResponse(BaseModel):
    """Dashboard 统计摘要响应。"""

    agents_total: int
    conversations_total: int
    team_executions_total: int


@router.get("/summary")
async def get_summary(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> DashboardSummaryResponse:
    """获取 Dashboard 统计摘要。

    ADMIN 角色可查看全部数据，普通用户只能查看自己的数据。
    """
    is_admin = current_user.role == "admin"

    # 构建各表 COUNT 查询
    agents_stmt = select(func.count()).select_from(AgentModel)
    conversations_stmt = select(func.count()).select_from(ConversationModel)
    team_executions_stmt = select(func.count()).select_from(TeamExecutionModel)

    # 非管理员只能查看自己的数据
    if not is_admin:
        agents_stmt = agents_stmt.where(AgentModel.owner_id == current_user.id)
        conversations_stmt = conversations_stmt.where(ConversationModel.user_id == current_user.id)
        team_executions_stmt = team_executions_stmt.where(TeamExecutionModel.user_id == current_user.id)

    # 并行执行 COUNT 查询
    agents_result, conversations_result, team_executions_result = await asyncio.gather(
        db.execute(agents_stmt),
        db.execute(conversations_stmt),
        db.execute(team_executions_stmt),
    )

    return DashboardSummaryResponse(
        agents_total=agents_result.scalar_one(),
        conversations_total=conversations_result.scalar_one(),
        team_executions_total=team_executions_result.scalar_one(),
    )
