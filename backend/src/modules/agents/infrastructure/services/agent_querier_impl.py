"""IAgentQuerier 的 agents 模块实现。"""

from src.modules.agents.domain import Agent, AgentStatus, IAgentRepository
from src.shared.domain import ActiveAgentInfo, IAgentQuerier


class AgentQuerierImpl(IAgentQuerier):
    """基于 agents 模块 Repository 的 IAgentQuerier 实现。"""

    def __init__(self, agent_repository: IAgentRepository) -> None:
        self._agent_repository = agent_repository

    async def get_active_agent(self, agent_id: int) -> ActiveAgentInfo | None:
        """Agent 不存在或非 ACTIVE 状态时返回 None。"""
        agent = await self._agent_repository.get_by_id(agent_id)
        if agent is None or agent.status != AgentStatus.ACTIVE:
            return None
        return self._to_active_agent_info(agent)

    @staticmethod
    def _to_active_agent_info(agent: Agent) -> ActiveAgentInfo:
        return ActiveAgentInfo(
            id=agent.id,  # type: ignore[arg-type]
            name=agent.name,
            system_prompt=agent.system_prompt,
            model_id=agent.config.model_id,
            temperature=agent.config.temperature,
            max_tokens=agent.config.max_tokens,
            top_p=agent.config.top_p,
            stop_sequences=agent.config.stop_sequences,
        )
