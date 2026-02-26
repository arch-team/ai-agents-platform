"""IAgentQuerier 的 agents 模块实现。"""

from typing import cast

from cachetools import TTLCache

from src.modules.agents.domain import Agent, AgentStatus, IAgentRepository
from src.shared.domain import ActiveAgentInfo, IAgentQuerier


class AgentQuerierImpl(IAgentQuerier):
    """基于 agents 模块 Repository 的 IAgentQuerier 实现, 内置 TTL 缓存。"""

    def __init__(
        self,
        agent_repository: IAgentRepository,
        *,
        cache_maxsize: int = 500,
        cache_ttl: int = 300,
    ) -> None:
        self._agent_repository = agent_repository
        self._cache: TTLCache[int, ActiveAgentInfo | None] = TTLCache(
            maxsize=cache_maxsize,
            ttl=cache_ttl,
        )

    async def get_active_agent(self, agent_id: int) -> ActiveAgentInfo | None:
        """Agent 不存在或非 ACTIVE 状态时返回 None, 结果缓存 5 分钟。"""
        if agent_id in self._cache:
            return cast("ActiveAgentInfo | None", self._cache[agent_id])

        agent = await self._agent_repository.get_by_id(agent_id)
        if agent is None or agent.status != AgentStatus.ACTIVE:
            self._cache[agent_id] = None
            return None

        info = self._to_active_agent_info(agent)
        self._cache[agent_id] = info
        return info

    def clear_cache(self) -> None:
        """清除缓存 (用于 Agent 配置更新后主动失效)。"""
        self._cache.clear()

    @staticmethod
    def _to_active_agent_info(agent: Agent) -> ActiveAgentInfo:
        if agent.id is None:
            msg = "Agent ID 不能为空"
            raise ValueError(msg)
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
        )
