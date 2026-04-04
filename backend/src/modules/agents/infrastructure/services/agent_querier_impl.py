"""IAgentQuerier 的 agents 模块实现。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from cachetools import TTLCache
from sqlalchemy import select


if TYPE_CHECKING:
    from collections.abc import Callable

from src.modules.agents.domain import Agent, AgentStatus, IAgentRepository
from src.modules.agents.infrastructure.persistence.models.agent_blueprint_model import AgentBlueprintModel
from src.shared.domain import ActiveAgentInfo, IAgentQuerier


# TESTING 和 ACTIVE 都是可执行状态
_QUERYABLE_STATUSES = frozenset({AgentStatus.TESTING, AgentStatus.ACTIVE})


class AgentQuerierImpl(IAgentQuerier):
    """基于 agents 模块 Repository 的 IAgentQuerier 实现, 内置 TTL 缓存。"""

    def __init__(
        self,
        agent_repository: IAgentRepository,
        session_factory: Callable[..., Any] | None = None,
        *,
        cache_maxsize: int = 500,
        cache_ttl: int = 300,
    ) -> None:
        self._agent_repository = agent_repository
        self._session_factory = session_factory
        self._cache: TTLCache[int, ActiveAgentInfo | None] = TTLCache(
            maxsize=cache_maxsize,
            ttl=cache_ttl,
        )

    async def get_active_agent(self, agent_id: int) -> ActiveAgentInfo | None:
        """Agent 不存在或非 TESTING/ACTIVE 状态时返回 None, 结果缓存 5 分钟。"""
        if agent_id in self._cache:
            return cast("ActiveAgentInfo | None", self._cache[agent_id])

        agent = await self._agent_repository.get_by_id(agent_id)
        if agent is None or agent.status not in _QUERYABLE_STATUSES:
            self._cache[agent_id] = None
            return None

        blueprint_data = await self._get_blueprint_data(agent.blueprint_id)
        info = self._to_active_agent_info(agent, blueprint_data)
        self._cache[agent_id] = info
        return info

    def clear_cache(self) -> None:
        """清除缓存 (用于 Agent 配置更新后主动失效)。"""
        self._cache.clear()

    async def _get_blueprint_data(self, blueprint_id: int | None) -> dict[str, str]:
        """从 Blueprint 表读取 workspace_path / runtime_arn / workspace_s3_uri。"""
        if blueprint_id is None or self._session_factory is None:
            return {}
        async with self._session_factory() as session:
            stmt = select(
                AgentBlueprintModel.workspace_path,
                AgentBlueprintModel.runtime_arn,
                AgentBlueprintModel.workspace_s3_uri,
            ).where(AgentBlueprintModel.id == blueprint_id)
            row = (await session.execute(stmt)).first()
            if row is None:
                return {}
            return {
                "workspace_path": row.workspace_path or "",
                "runtime_arn": row.runtime_arn or "",
                "workspace_s3_uri": row.workspace_s3_uri or "",
            }

    @staticmethod
    def _to_active_agent_info(agent: Agent, blueprint_data: dict[str, str] | None = None) -> ActiveAgentInfo:
        if agent.id is None:
            msg = "Agent ID 不能为空"
            raise ValueError(msg)
        bp = blueprint_data or {}
        return ActiveAgentInfo(
            id=agent.id,
            name=agent.name,
            system_prompt=agent.system_prompt,
            model_id=agent.config.model_id,
            temperature=agent.config.temperature,
            max_tokens=agent.config.max_tokens,
            top_p=agent.config.top_p,
            stop_sequences=agent.config.stop_sequences,
            runtime_type=agent.config.runtime_type,
            enable_teams=agent.config.enable_teams,
            enable_memory=agent.config.enable_memory,
            tool_ids=agent.config.tool_ids,
            workspace_path=bp.get("workspace_path", ""),
            runtime_arn=bp.get("runtime_arn", ""),
            workspace_s3_uri=bp.get("workspace_s3_uri", ""),
        )
