"""Agent 仓库实现。"""

import json

from sqlalchemy import func, select

from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.modules.agents.infrastructure.persistence.models.agent_model import AgentModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class AgentRepositoryImpl(PydanticRepository[Agent, AgentModel, int], IAgentRepository):
    """Agent 仓库的 SQLAlchemy 实现。"""

    entity_class = Agent
    model_class = AgentModel
    _updatable_fields: frozenset[str] = frozenset(
        {
            "name",
            "description",
            "system_prompt",
            "status",
            "model_id",
            "temperature",
            "max_tokens",
            "top_p",
            "stop_sequences",
        },
    )

    def _to_entity(self, model: AgentModel) -> Agent:
        stop_sequences: tuple[str, ...] = ()
        if model.stop_sequences:
            stop_sequences = tuple(json.loads(model.stop_sequences))
        config = AgentConfig(
            model_id=model.model_id,
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            top_p=model.top_p,
            stop_sequences=stop_sequences,
        )
        return Agent(
            id=model.id,
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            status=AgentStatus(model.status),
            owner_id=model.owner_id,
            config=config,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Agent) -> AgentModel:
        stop_sequences_json = json.dumps(list(entity.config.stop_sequences)) if entity.config.stop_sequences else ""
        return AgentModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            system_prompt=entity.system_prompt,
            status=entity.status.value,
            owner_id=entity.owner_id,
            model_id=entity.config.model_id,
            temperature=entity.config.temperature,
            max_tokens=entity.config.max_tokens,
            top_p=entity.config.top_p,
            stop_sequences=stop_sequences_json,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _get_update_data(self, entity: Agent) -> dict[str, object]:
        """提取可更新字段数据，展开 AgentConfig。"""
        stop_sequences_json = json.dumps(list(entity.config.stop_sequences)) if entity.config.stop_sequences else ""
        flat_data: dict[str, object] = {
            "name": entity.name,
            "description": entity.description,
            "system_prompt": entity.system_prompt,
            "status": entity.status.value,
            "model_id": entity.config.model_id,
            "temperature": entity.config.temperature,
            "max_tokens": entity.config.max_tokens,
            "top_p": entity.config.top_p,
            "stop_sequences": stop_sequences_json,
        }
        return {k: v for k, v in flat_data.items() if k in self._updatable_fields}

    async def list_by_owner(  # noqa: D102
        self,
        owner_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Agent]:
        stmt = (
            select(AgentModel)
            .where(AgentModel.owner_id == owner_id)
            .offset(offset)
            .limit(limit)
            .order_by(AgentModel.id)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_owner(self, owner_id: int) -> int:  # noqa: D102
        stmt = select(func.count()).select_from(AgentModel).where(AgentModel.owner_id == owner_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_by_name_and_owner(  # noqa: D102
        self,
        name: str,
        owner_id: int,
    ) -> Agent | None:
        stmt = select(AgentModel).where(
            AgentModel.name == name,
            AgentModel.owner_id == owner_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_owner_and_status(  # noqa: D102
        self,
        owner_id: int,
        status: AgentStatus,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Agent]:
        stmt = (
            select(AgentModel)
            .where(
                AgentModel.owner_id == owner_id,
                AgentModel.status == status.value,
            )
            .offset(offset)
            .limit(limit)
            .order_by(AgentModel.id)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_owner_and_status(  # noqa: D102
        self,
        owner_id: int,
        status: AgentStatus,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(AgentModel)
            .where(
                AgentModel.owner_id == owner_id,
                AgentModel.status == status.value,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
