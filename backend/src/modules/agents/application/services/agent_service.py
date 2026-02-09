"""Agent 应用服务。"""

from src.modules.agents.application.dto.agent_dto import (
    AgentDTO,
    CreateAgentDTO,
    PagedAgentDTO,
    UpdateAgentDTO,
)
from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.events import (
    AgentActivatedEvent,
    AgentArchivedEvent,
    AgentCreatedEvent,
    AgentDeletedEvent,
    AgentUpdatedEvent,
)
from src.modules.agents.domain.exceptions import (
    AgentNameDuplicateError,
    AgentNotFoundError,
)
from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.event_bus import event_bus
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError


class AgentService:
    """Agent 业务服务，编排 Agent 的 CRUD 和状态变更用例。"""

    def __init__(self, repository: IAgentRepository) -> None:
        self._repository = repository

    async def create_agent(self, dto: CreateAgentDTO, owner_id: int) -> AgentDTO:
        """创建 Agent（默认 DRAFT）。同 owner 下名称不可重复。

        Raises:
            AgentNameDuplicateError: 名称重复
        """
        existing = await self._repository.get_by_name_and_owner(dto.name, owner_id)
        if existing is not None:
            raise AgentNameDuplicateError(dto.name)

        agent = Agent(
            name=dto.name,
            description=dto.description,
            system_prompt=dto.system_prompt,
            owner_id=owner_id,
            config=AgentConfig(
                model_id=dto.model_id,
                temperature=dto.temperature,
                max_tokens=dto.max_tokens,
            ),
        )
        created = await self._repository.create(agent)
        await event_bus.publish_async(
            AgentCreatedEvent(
                agent_id=created.id or 0,
                owner_id=owner_id,
                name=created.name,
            ),
        )
        return self._to_dto(created)

    async def get_agent(self, agent_id: int) -> AgentDTO:
        """获取 Agent 详情。

        Raises:
            AgentNotFoundError: Agent 不存在
        """
        agent = await self._repository.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)
        return self._to_dto(agent)

    async def list_agents(
        self,
        owner_id: int,
        *,
        status: AgentStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedAgentDTO:
        """获取用户的 Agent 列表（支持按状态筛选）。"""
        offset = (page - 1) * page_size

        if status is not None:
            agents = await self._repository.list_by_owner_and_status(
                owner_id,
                status,
                offset=offset,
                limit=page_size,
            )
            total = await self._repository.count_by_owner_and_status(owner_id, status)
        else:
            agents = await self._repository.list_by_owner(
                owner_id,
                offset=offset,
                limit=page_size,
            )
            total = await self._repository.count_by_owner(owner_id)

        return PagedAgentDTO(
            items=[self._to_dto(a) for a in agents],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_agent(
        self,
        agent_id: int,
        dto: UpdateAgentDTO,
        operator_id: int,
    ) -> AgentDTO:
        """更新 Agent。仅 owner 可操作，仅 DRAFT 可编辑全部字段。

        Raises:
            AgentNotFoundError: Agent 不存在
            DomainError: 非 owner 操作
            InvalidStateTransitionError: 非 DRAFT 状态不允许更新
            AgentNameDuplicateError: 名称重复
        """
        agent = await self._repository.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)

        self._check_permission(agent, operator_id)

        if agent.status != AgentStatus.DRAFT:
            raise InvalidStateTransitionError(
                entity_type="Agent",
                current_state=agent.status.value,
                target_state="updated",
            )

        changed_fields: list[str] = []

        # 检查名称重复
        if dto.name is not None and dto.name != agent.name:
            existing = await self._repository.get_by_name_and_owner(
                dto.name,
                agent.owner_id,
            )
            if existing is not None:
                raise AgentNameDuplicateError(dto.name)
            agent.name = dto.name
            changed_fields.append("name")

        if dto.description is not None:
            agent.description = dto.description
            changed_fields.append("description")

        if dto.system_prompt is not None:
            agent.system_prompt = dto.system_prompt
            changed_fields.append("system_prompt")

        # 重建 AgentConfig (如果有 config 字段变化)
        config_changed = False
        new_model_id = agent.config.model_id
        new_temperature = agent.config.temperature
        new_max_tokens = agent.config.max_tokens

        if dto.model_id is not None:
            new_model_id = dto.model_id
            config_changed = True
            changed_fields.append("model_id")
        if dto.temperature is not None:
            new_temperature = dto.temperature
            config_changed = True
            changed_fields.append("temperature")
        if dto.max_tokens is not None:
            new_max_tokens = dto.max_tokens
            config_changed = True
            changed_fields.append("max_tokens")

        if config_changed:
            agent.config = AgentConfig(
                model_id=new_model_id,
                temperature=new_temperature,
                max_tokens=new_max_tokens,
                top_p=agent.config.top_p,
                stop_sequences=agent.config.stop_sequences,
            )

        agent.touch()
        updated = await self._repository.update(agent)

        if changed_fields:
            await event_bus.publish_async(
                AgentUpdatedEvent(
                    agent_id=updated.id or 0,
                    owner_id=updated.owner_id,
                    changed_fields=tuple(changed_fields),
                ),
            )

        return self._to_dto(updated)

    async def delete_agent(self, agent_id: int, operator_id: int) -> None:
        """删除 Agent。仅 DRAFT 可删除。

        Raises:
            AgentNotFoundError: Agent 不存在
            DomainError: 非 owner 操作
            InvalidStateTransitionError: 非 DRAFT 状态不允许删除
        """
        agent = await self._repository.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)

        self._check_permission(agent, operator_id)

        if agent.status != AgentStatus.DRAFT:
            raise InvalidStateTransitionError(
                entity_type="Agent",
                current_state=agent.status.value,
                target_state="deleted",
            )

        await self._repository.delete(agent_id)

        await event_bus.publish_async(
            AgentDeletedEvent(
                agent_id=agent_id,
                owner_id=agent.owner_id,
            ),
        )

    async def activate_agent(self, agent_id: int, operator_id: int) -> AgentDTO:
        """激活 Agent。调用 agent.activate() 进行状态转换和校验。

        Raises:
            AgentNotFoundError: Agent 不存在
            DomainError: 非 owner 操作
            InvalidStateTransitionError: 非 DRAFT 状态
            ValidationError: 缺少 system_prompt
        """
        agent = await self._repository.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)

        self._check_permission(agent, operator_id)

        agent.activate()
        updated = await self._repository.update(agent)

        await event_bus.publish_async(
            AgentActivatedEvent(
                agent_id=updated.id or 0,
                owner_id=updated.owner_id,
            ),
        )
        return self._to_dto(updated)

    async def archive_agent(self, agent_id: int, operator_id: int) -> AgentDTO:
        """归档 Agent。调用 agent.archive() 进行状态转换。

        Raises:
            AgentNotFoundError: Agent 不存在
            DomainError: 非 owner 操作
            InvalidStateTransitionError: 已归档状态不可重复归档
        """
        agent = await self._repository.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)

        self._check_permission(agent, operator_id)

        agent.archive()
        updated = await self._repository.update(agent)

        await event_bus.publish_async(
            AgentArchivedEvent(
                agent_id=updated.id or 0,
                owner_id=updated.owner_id,
            ),
        )
        return self._to_dto(updated)

    @staticmethod
    def _to_dto(agent: Agent) -> AgentDTO:
        return AgentDTO(
            id=agent.id or 0,
            name=agent.name,
            description=agent.description,
            system_prompt=agent.system_prompt,
            status=agent.status.value,
            owner_id=agent.owner_id,
            model_id=agent.config.model_id,
            temperature=agent.config.temperature,
            max_tokens=agent.config.max_tokens,
            top_p=agent.config.top_p,
            created_at=agent.created_at or agent.updated_at,  # type: ignore[arg-type]
            updated_at=agent.updated_at,  # type: ignore[arg-type]
        )

    @staticmethod
    def _check_permission(agent: Agent, operator_id: int) -> None:
        """检查操作者是否为 Agent 所有者。

        Raises:
            DomainError: 操作者非 Agent 所有者
        """
        if agent.owner_id != operator_id:
            raise DomainError(
                message="无权操作此 Agent",
                code="FORBIDDEN_AGENT",
            )
