"""Agent 仓库实现。"""

import json
from collections.abc import Sequence

from sqlalchemy import ColumnElement, select

from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.modules.agents.infrastructure.persistence.models.agent_model import AgentModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


def _serialize_stop_sequences(sequences: tuple[str, ...]) -> str:
    return json.dumps(list(sequences)) if sequences else ""


def _deserialize_stop_sequences(raw: str) -> tuple[str, ...]:
    return tuple(json.loads(raw)) if raw else ()


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
        return Agent(
            id=model.id,
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            status=AgentStatus(model.status),
            owner_id=model.owner_id,
            config=AgentConfig(
                model_id=model.model_id,
                temperature=model.temperature,
                max_tokens=model.max_tokens,
                top_p=model.top_p,
                stop_sequences=_deserialize_stop_sequences(model.stop_sequences),
            ),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _flatten_config(self, entity: Agent) -> dict[str, object]:
        return {
            "name": entity.name,
            "description": entity.description,
            "system_prompt": entity.system_prompt,
            "status": entity.status.value,
            "model_id": entity.config.model_id,
            "temperature": entity.config.temperature,
            "max_tokens": entity.config.max_tokens,
            "top_p": entity.config.top_p,
            "stop_sequences": _serialize_stop_sequences(entity.config.stop_sequences),
        }

    def _to_model(self, entity: Agent) -> AgentModel:
        return AgentModel(
            id=entity.id,
            owner_id=entity.owner_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            **self._flatten_config(entity),
        )

    def _get_update_data(self, entity: Agent) -> dict[str, object]:
        return self._flatten_config(entity)

    # ── 查询辅助方法 ──

    @staticmethod
    def _owner_filters(
        owner_id: int,
        status: AgentStatus | None = None,
    ) -> Sequence[ColumnElement[bool]]:
        """构建 owner 相关的查询条件。"""
        filters: list[ColumnElement[bool]] = [AgentModel.owner_id == owner_id]
        if status is not None:
            filters.append(AgentModel.status == status.value)
        return filters

    # ── 接口实现 ──

    async def list_by_owner(  # noqa: D102
        self,
        owner_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Agent]:
        return await self._list_where(
            *self._owner_filters(owner_id),
            offset=offset,
            limit=limit,
        )

    async def count_by_owner(self, owner_id: int) -> int:  # noqa: D102
        return await self._count_where(*self._owner_filters(owner_id))

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
        return await self._list_where(
            *self._owner_filters(owner_id, status),
            offset=offset,
            limit=limit,
        )

    async def count_by_owner_and_status(  # noqa: D102
        self,
        owner_id: int,
        status: AgentStatus,
    ) -> int:
        return await self._count_where(*self._owner_filters(owner_id, status))
