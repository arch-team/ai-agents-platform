"""Agent Blueprint 仓库实现。"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.agents.domain.repositories.agent_blueprint_repository import (
    BlueprintRuntimeInfo,
    IAgentBlueprintRepository,
)
from src.modules.agents.infrastructure.persistence.models.agent_blueprint_model import (
    AgentBlueprintModel,
)


class AgentBlueprintRepositoryImpl(IAgentBlueprintRepository):
    """Agent Blueprint 仓库的 SQLAlchemy 实现。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_runtime_info(self, agent_id: int) -> BlueprintRuntimeInfo | None:
        stmt = select(
            AgentBlueprintModel.id,
            AgentBlueprintModel.workspace_path,
            AgentBlueprintModel.runtime_arn,
            AgentBlueprintModel.workspace_s3_uri,
        ).where(AgentBlueprintModel.agent_id == agent_id)

        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None

        return BlueprintRuntimeInfo(
            blueprint_id=row[0],
            workspace_path=row[1],
            runtime_arn=row[2],
            workspace_s3_uri=row[3],
        )

    async def update_runtime_info(
        self,
        agent_id: int,
        *,
        runtime_arn: str,
        workspace_s3_uri: str,
    ) -> None:
        stmt = (
            update(AgentBlueprintModel)
            .where(AgentBlueprintModel.agent_id == agent_id)
            .values(runtime_arn=runtime_arn, workspace_s3_uri=workspace_s3_uri)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def clear_runtime_info(self, agent_id: int) -> None:
        stmt = (
            update(AgentBlueprintModel)
            .where(AgentBlueprintModel.agent_id == agent_id)
            .values(runtime_arn="", workspace_s3_uri="")
        )
        await self._session.execute(stmt)
        await self._session.flush()
