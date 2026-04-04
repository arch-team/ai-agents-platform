"""Agent 应用服务。"""

import asyncio
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import structlog

from src.modules.agents.application.dto.agent_dto import (
    AgentDTO,
    CreateAgentDTO,
    UpdateAgentDTO,
)
from src.modules.agents.application.interfaces.agent_runtime_manager import IAgentRuntimeManager
from src.modules.agents.application.interfaces.workspace_manager import IWorkspaceManager
from src.modules.agents.domain.entities.agent import Agent
from src.modules.agents.domain.events import (
    AgentActivatedEvent,
    AgentArchivedEvent,
    AgentCreatedEvent,
    AgentDeletedEvent,
    AgentGoLiveEvent,
    AgentTakenOfflineEvent,
    AgentTestingStartedEvent,
    AgentUpdatedEvent,
    BaseAgentEvent,
)
from src.modules.agents.domain.exceptions import (
    AgentNameDuplicateError,
    AgentNotFoundError,
)
from src.modules.agents.domain.repositories.agent_blueprint_repository import IAgentBlueprintRepository
from src.modules.agents.domain.repositories.agent_repository import IAgentRepository
from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.application.dtos import PagedResult
from src.shared.application.ownership import check_ownership, get_or_raise
from src.shared.domain.event_bus import event_bus
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError


logger = structlog.get_logger(__name__)


class AgentService:
    """Agent 业务服务，编排 Agent 的 CRUD 和状态变更用例。"""

    def __init__(
        self,
        repository: IAgentRepository,
        blueprint_repository: IAgentBlueprintRepository | None = None,
        workspace_manager: IWorkspaceManager | None = None,
        runtime_manager: IAgentRuntimeManager | None = None,
    ) -> None:
        self._repository = repository
        self._blueprint_repo = blueprint_repository
        self._workspace_manager = workspace_manager
        self._runtime_manager = runtime_manager

    async def create_agent(self, dto: CreateAgentDTO, owner_id: int) -> AgentDTO:
        """创建 Agent（默认 DRAFT）。同 owner 下名称不可重复。

        Raises:
            AgentNameDuplicateError: 名称重复
        """
        await self._check_name_unique(dto.name, owner_id)

        agent = Agent(
            name=dto.name,
            description=dto.description,
            system_prompt=dto.system_prompt,
            owner_id=owner_id,
            config=AgentConfig(
                model_id=dto.model_id,
                temperature=dto.temperature,
                max_tokens=dto.max_tokens,
                runtime_type=dto.runtime_type,
                enable_teams=dto.enable_teams,
                enable_memory=dto.enable_memory,
                tool_ids=tuple(dto.tool_ids),
            ),
        )
        created = await self._repository.create(agent)
        if created.id is None:
            msg = "Agent 创建后 ID 不能为空"
            raise ValueError(msg)
        await event_bus.publish_async(
            AgentCreatedEvent(
                agent_id=created.id,
                owner_id=owner_id,
                name=created.name,
            ),
        )
        return self._to_dto(created)

    async def get_agent(self, agent_id: int) -> AgentDTO:
        """Raises: AgentNotFoundError"""
        agent = await self._get_agent_or_raise(agent_id)
        return self._to_dto(agent)

    async def get_owned_agent(self, agent_id: int, operator_id: int) -> AgentDTO:
        """获取 Agent 详情（校验所有权）。

        Raises:
            AgentNotFoundError, DomainError(FORBIDDEN_AGENT)
        """
        agent = await self._get_owned_agent(agent_id, operator_id)
        return self._to_dto(agent)

    async def list_agents(
        self,
        owner_id: int,
        *,
        status: AgentStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[AgentDTO]:
        """获取用户的 Agent 列表，支持按状态筛选和分页。"""
        offset = (page - 1) * page_size

        if status is not None:
            agents, total = await asyncio.gather(
                self._repository.list_by_owner_and_status(owner_id, status, offset=offset, limit=page_size),
                self._repository.count_by_owner_and_status(owner_id, status),
            )
        else:
            agents, total = await asyncio.gather(
                self._repository.list_by_owner(owner_id, offset=offset, limit=page_size),
                self._repository.count_by_owner(owner_id),
            )

        return PagedResult(
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
            AgentNotFoundError, DomainError, InvalidStateTransitionError,
            AgentNameDuplicateError
        """
        agent = await self._get_owned_agent(agent_id, operator_id)

        if agent.status != AgentStatus.DRAFT:
            raise InvalidStateTransitionError(
                entity_type="Agent",
                current_state=agent.status.value,
                target_state="updated",
            )

        changed_fields = await self._apply_agent_updates(agent, dto)
        agent.touch()
        updated = await self._repository.update(agent)

        if changed_fields:
            if updated.id is None:
                msg = "Agent 更新后 ID 不能为空"
                raise ValueError(msg)
            await event_bus.publish_async(
                AgentUpdatedEvent(
                    agent_id=updated.id,
                    owner_id=updated.owner_id,
                    changed_fields=tuple(changed_fields),
                ),
            )

        return self._to_dto(updated)

    async def _apply_agent_updates(self, agent: Agent, dto: UpdateAgentDTO) -> list[str]:
        """应用 DTO 中非 None 的字段到 Agent 实体, 返回变更字段列表。"""
        changed_fields: list[str] = []

        # 名称变更需要唯一性校验
        if dto.name is not None and dto.name != agent.name:
            await self._check_name_unique(dto.name, agent.owner_id)
            agent.name = dto.name
            changed_fields.append("name")

        # 普通字段更新
        for field in ("description", "system_prompt"):
            value = getattr(dto, field)
            if value is not None:
                setattr(agent, field, value)
                changed_fields.append(field)

        # 重建 AgentConfig (frozen 值对象, 任一字段变化需整体替换)
        config_overrides: dict[str, object] = {}
        for field in ("model_id", "temperature", "max_tokens", "runtime_type", "enable_teams", "enable_memory"):
            value = getattr(dto, field)
            if value is not None:
                config_overrides[field] = value
                changed_fields.append(field)

        if dto.tool_ids is not None:
            config_overrides["tool_ids"] = tuple(dto.tool_ids)
            changed_fields.append("tool_ids")

        if config_overrides:
            agent.config = replace(agent.config, **config_overrides)  # type: ignore[arg-type]

        return changed_fields

    async def delete_agent(self, agent_id: int, operator_id: int) -> None:
        """删除 Agent。仅 DRAFT 可删除。

        Raises:
            AgentNotFoundError, DomainError, InvalidStateTransitionError
        """
        agent = await self._get_owned_agent(agent_id, operator_id)

        if agent.status != AgentStatus.DRAFT:
            raise InvalidStateTransitionError(
                entity_type="Agent",
                current_state=agent.status.value,
                target_state="deleted",
            )

        await self._repository.delete(agent_id)
        await event_bus.publish_async(
            AgentDeletedEvent(agent_id=agent_id, owner_id=agent.owner_id),
        )

    async def activate_agent(self, agent_id: int, operator_id: int) -> AgentDTO:
        """激活 Agent。调用 agent.activate() 进行状态转换和校验。

        Raises:
            AgentNotFoundError, DomainError, InvalidStateTransitionError,
            ValidationError
        """
        return await self._transition_state(
            agent_id,
            operator_id,
            Agent.activate,
            AgentActivatedEvent,
        )

    async def archive_agent(self, agent_id: int, operator_id: int) -> AgentDTO:
        """归档 Agent。调用 agent.archive() 进行状态转换。

        Raises:
            AgentNotFoundError, DomainError, InvalidStateTransitionError
        """
        return await self._transition_state(
            agent_id,
            operator_id,
            Agent.archive,
            AgentArchivedEvent,
        )

    # ── Blueprint 生命周期编排 ──

    async def start_testing(self, agent_id: int, operator_id: int) -> AgentDTO:
        """开始测试: DRAFT → TESTING。

        编排流程:
        1. 校验 DRAFT 状态 + Blueprint 存在
        2. WorkspaceManager.upload_to_s3() → 获取 S3 URI
        3. AgentRuntimeManager.provision() → 获取 runtime_arn
        4. 保存 runtime_arn 到 Blueprint
        5. Agent → TESTING

        Raises:
            AgentNotFoundError, DomainError, InvalidStateTransitionError
        """
        self._require_blueprint_deps()
        assert self._blueprint_repo is not None
        assert self._workspace_manager is not None
        assert self._runtime_manager is not None

        agent = await self._get_owned_agent(agent_id, operator_id)
        agent.start_testing()

        blueprint_info = await self._blueprint_repo.get_runtime_info(agent_id)
        if blueprint_info is None:
            raise DomainError(message="Agent 没有 Blueprint, 无法开始测试", code="BLUEPRINT_NOT_FOUND")
        if not blueprint_info.workspace_path:
            raise DomainError(message="Agent 工作目录未创建, 无法开始测试", code="WORKSPACE_NOT_FOUND")

        workspace_s3_uri = await self._workspace_manager.upload_to_s3(
            Path(blueprint_info.workspace_path),
            agent_id,
        )

        try:
            runtime_info = await self._runtime_manager.provision(agent_id, workspace_s3_uri)
        except Exception:
            logger.exception("start_testing_provision_failed", agent_id=agent_id)
            raise

        await self._blueprint_repo.update_runtime_info(
            agent_id,
            runtime_arn=runtime_info.runtime_arn,
            workspace_s3_uri=workspace_s3_uri,
        )

        updated = await self._repository.update(agent)
        if updated.id is None:
            msg = "Agent 状态变更后 ID 不能为空"
            raise ValueError(msg)

        await event_bus.publish_async(
            AgentTestingStartedEvent(
                agent_id=updated.id,
                owner_id=updated.owner_id,
                runtime_arn=runtime_info.runtime_arn,
            ),
        )

        logger.info("agent_testing_started", agent_id=agent_id, runtime_arn=runtime_info.runtime_arn)
        return self._to_dto(updated)

    async def go_live(self, agent_id: int, operator_id: int) -> AgentDTO:
        """上线发布: TESTING → ACTIVE。同一 Runtime，开放给最终用户。

        Raises:
            AgentNotFoundError, DomainError, InvalidStateTransitionError
        """
        agent = await self._get_owned_agent(agent_id, operator_id)
        agent.activate()
        updated = await self._repository.update(agent)
        if updated.id is None:
            msg = "Agent 状态变更后 ID 不能为空"
            raise ValueError(msg)
        await event_bus.publish_async(
            AgentGoLiveEvent(agent_id=updated.id, owner_id=updated.owner_id),
        )
        logger.info("agent_go_live", agent_id=agent_id)
        return self._to_dto(updated)

    async def take_offline(self, agent_id: int, operator_id: int) -> AgentDTO:
        """下线归档: ACTIVE → ARCHIVED。销毁 Runtime 释放资源。

        Raises:
            AgentNotFoundError, DomainError, InvalidStateTransitionError
        """
        self._require_blueprint_deps()
        assert self._blueprint_repo is not None
        assert self._runtime_manager is not None

        agent = await self._get_owned_agent(agent_id, operator_id)
        blueprint_info = await self._blueprint_repo.get_runtime_info(agent_id)
        runtime_arn = blueprint_info.runtime_arn if blueprint_info else ""

        agent.archive()
        updated = await self._repository.update(agent)
        if updated.id is None:
            msg = "Agent 状态变更后 ID 不能为空"
            raise ValueError(msg)

        if runtime_arn:
            try:
                await self._runtime_manager.deprovision(runtime_arn)
                await self._blueprint_repo.clear_runtime_info(agent_id)
            except Exception:
                logger.exception("take_offline_deprovision_failed", agent_id=agent_id, runtime_arn=runtime_arn)

        await event_bus.publish_async(
            AgentTakenOfflineEvent(agent_id=updated.id, owner_id=updated.owner_id),
        )
        logger.info("agent_taken_offline", agent_id=agent_id)
        return self._to_dto(updated)

    def _require_blueprint_deps(self) -> None:
        """校验 Blueprint 相关依赖已注入。"""
        if self._blueprint_repo is None or self._workspace_manager is None or self._runtime_manager is None:
            raise DomainError(
                message="Blueprint 生命周期管理依赖未注入",
                code="MISSING_BLUEPRINT_DEPS",
            )

    # ── 内部辅助方法 ──

    async def _transition_state(
        self,
        agent_id: int,
        operator_id: int,
        action: Callable[[Agent], None],
        event_cls: type[BaseAgentEvent],
    ) -> AgentDTO:
        """状态变更通用流程：获取 -> 校验所有权 -> 执行动作 -> 持久化 -> 发布事件。"""
        agent = await self._get_owned_agent(agent_id, operator_id)
        action(agent)
        updated = await self._repository.update(agent)
        if updated.id is None:
            msg = "Agent 状态变更后 ID 不能为空"
            raise ValueError(msg)
        await event_bus.publish_async(
            event_cls(agent_id=updated.id, owner_id=updated.owner_id),
        )
        return self._to_dto(updated)

    async def _get_agent_or_raise(self, agent_id: int) -> Agent:
        return await get_or_raise(self._repository, agent_id, AgentNotFoundError, agent_id)

    async def _get_owned_agent(self, agent_id: int, operator_id: int) -> Agent:
        agent = await self._get_agent_or_raise(agent_id)
        check_ownership(agent, operator_id, error_code="FORBIDDEN_AGENT")
        return agent

    async def _check_name_unique(self, name: str, owner_id: int) -> None:
        existing = await self._repository.get_by_name_and_owner(name, owner_id)
        if existing is not None:
            raise AgentNameDuplicateError(name)

    @staticmethod
    def _to_dto(agent: Agent) -> AgentDTO:
        id_, created_at, updated_at = agent.require_persisted()
        return AgentDTO(
            id=id_,
            name=agent.name,
            description=agent.description,
            system_prompt=agent.system_prompt,
            status=agent.status.value,
            owner_id=agent.owner_id,
            model_id=agent.config.model_id,
            temperature=agent.config.temperature,
            max_tokens=agent.config.max_tokens,
            top_p=agent.config.top_p,
            runtime_type=agent.config.runtime_type,
            enable_teams=agent.config.enable_teams,
            enable_memory=agent.config.enable_memory,
            created_at=created_at,
            updated_at=updated_at,
            tool_ids=list(agent.config.tool_ids),
        )
