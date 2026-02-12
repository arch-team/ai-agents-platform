"""TeamExecution 仓库实现。"""

from sqlalchemy import select

from src.modules.execution.domain.entities.team_execution import TeamExecution
from src.modules.execution.domain.entities.team_execution_log import TeamExecutionLog
from src.modules.execution.domain.repositories.team_execution_repository import (
    ITeamExecutionLogRepository,
    ITeamExecutionRepository,
)
from src.modules.execution.domain.value_objects.team_execution_status import (
    TeamExecutionStatus,
)
from src.modules.execution.infrastructure.persistence.models.team_execution_log_model import (
    TeamExecutionLogModel,
)
from src.modules.execution.infrastructure.persistence.models.team_execution_model import (
    TeamExecutionModel,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class TeamExecutionRepositoryImpl(
    PydanticRepository[TeamExecution, TeamExecutionModel, int],
    ITeamExecutionRepository,
):
    """TeamExecution 仓库的 SQLAlchemy 实现。"""

    entity_class = TeamExecution
    model_class = TeamExecutionModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "status",
            "result",
            "error_message",
            "input_tokens",
            "output_tokens",
            "started_at",
            "completed_at",
        },
    )

    def _to_entity(self, model: TeamExecutionModel) -> TeamExecution:
        """ORM Model -> Entity 转换，处理 status 枚举映射。"""
        data = {c.key: getattr(model, c.key) for c in model.__table__.columns}
        data["status"] = TeamExecutionStatus(data["status"])
        # MySQL TEXT 列 nullable=True, Entity 中 result/error_message 默认空字符串
        data["result"] = data["result"] or ""
        data["error_message"] = data["error_message"] or ""
        return TeamExecution.model_validate(data)

    async def list_by_user(  # noqa: D102
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TeamExecution]:
        stmt = (
            select(TeamExecutionModel)
            .where(TeamExecutionModel.user_id == user_id)
            .offset(offset)
            .limit(limit)
            .order_by(TeamExecutionModel.id.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_agent(  # noqa: D102
        self,
        agent_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TeamExecution]:
        stmt = (
            select(TeamExecutionModel)
            .where(TeamExecutionModel.agent_id == agent_id)
            .offset(offset)
            .limit(limit)
            .order_by(TeamExecutionModel.id.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_user(self, user_id: int) -> int:  # noqa: D102
        return await self._count_where(TeamExecutionModel.user_id == user_id)


class TeamExecutionLogRepositoryImpl(
    PydanticRepository[TeamExecutionLog, TeamExecutionLogModel, int],
    ITeamExecutionLogRepository,
):
    """TeamExecutionLog 仓库的 SQLAlchemy 实现。"""

    entity_class = TeamExecutionLog
    model_class = TeamExecutionLogModel
    _updatable_fields: frozenset[str] = frozenset({"content"})

    def _to_entity(self, model: TeamExecutionLogModel) -> TeamExecutionLog:
        """ORM Model -> Entity 转换，处理 TEXT nullable 映射。"""
        data = {c.key: getattr(model, c.key) for c in model.__table__.columns}
        data["content"] = data["content"] or ""
        return TeamExecutionLog.model_validate(data)

    async def list_by_execution(  # noqa: D102
        self,
        execution_id: int,
        *,
        after_sequence: int = 0,
    ) -> list[TeamExecutionLog]:
        stmt = (
            select(TeamExecutionLogModel)
            .where(
                TeamExecutionLogModel.execution_id == execution_id,
                TeamExecutionLogModel.sequence > after_sequence,
            )
            .order_by(TeamExecutionLogModel.sequence.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def append_log(self, log: TeamExecutionLog) -> TeamExecutionLog:  # noqa: D102
        return await self.create(log)
