"""Builder 应用服务。"""

import json
from collections.abc import AsyncIterator

import structlog

from src.modules.builder.application.dto.builder_dto import BuilderSessionDTO, TriggerBuilderDTO
from src.modules.builder.application.interfaces.builder_llm_service import IBuilderLLMService
from src.modules.builder.domain.entities.builder_session import BuilderSession
from src.modules.builder.domain.exceptions import BuilderSessionNotFoundError
from src.modules.builder.domain.repositories.builder_session_repository import IBuilderSessionRepository
from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.shared.application.ownership import check_ownership
from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.domain.interfaces.agent_creator import CreateAgentRequest, IAgentCreator


log = structlog.get_logger(__name__)


class BuilderService:
    """Builder 业务服务，编排 Agent 配置生成和确认创建流程。"""

    def __init__(
        self,
        session_repo: IBuilderSessionRepository,
        llm_service: IBuilderLLMService,
        agent_creator: IAgentCreator,
    ) -> None:
        self._session_repo = session_repo
        self._llm_service = llm_service
        self._agent_creator = agent_creator

    async def create_session(self, dto: TriggerBuilderDTO, user_id: int) -> BuilderSessionDTO:
        """创建 Builder 会话（PENDING 状态）。"""
        session = BuilderSession(user_id=user_id, prompt=dto.prompt)
        created = await self._session_repo.create(session)
        log.info("builder_session_created", session_id=created.id, user_id=user_id)
        return BuilderSessionDTO.from_entity(created)

    async def generate_config_stream(self, session_id: int, user_id: int) -> AsyncIterator[str]:
        """SSE 流式生成 Agent 配置。

        PENDING -> GENERATING -> CONFIRMED (成功) / 保持 GENERATING (失败)
        """
        session = await self._get_owned_session(session_id, user_id)
        session.start_generation()
        session = await self._session_repo.update(session)

        chunks: list[str] = []

        async for chunk in self._llm_service.generate_config(session.prompt):
            chunks.append(chunk)
            yield chunk

        # 尝试解析完整的生成结果 (LLM 可能用 markdown 代码围栏包裹 JSON)
        full_text = "".join(chunks).strip()
        if full_text.startswith("```"):
            full_text = full_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            config = json.loads(full_text)
            name = str(config.get("name", "未命名 Agent"))
            session.complete_generation(config=config, name=name)
            await self._session_repo.update(session)
            log.info("builder_generation_completed", session_id=session_id)
        except (json.JSONDecodeError, TypeError) as e:
            log.warning("builder_generation_parse_failed", session_id=session_id, error=str(e))

    async def confirm_session(
        self,
        session_id: int,
        user_id: int,
        *,
        name_override: str | None = None,
    ) -> BuilderSessionDTO:
        """确认会话并创建 Agent。

        Raises:
            BuilderSessionNotFoundError: 会话不存在
            ForbiddenError: 无权操作
            InvalidStateTransitionError: 会话不是 CONFIRMED 状态
        """
        session = await self._get_owned_session(session_id, user_id)

        if session.status != BuilderStatus.CONFIRMED:
            raise InvalidStateTransitionError(
                entity_type="BuilderSession",
                current_state=session.status.value,
                target_state="confirm_creation",
            )

        if session.generated_config is None:
            raise InvalidStateTransitionError(
                entity_type="BuilderSession",
                current_state=session.status.value,
                target_state="confirm_creation",
            )

        # 从生成的配置构造跨模块 CreateAgentRequest
        config = session.generated_config
        agent_name = name_override or str(config.get("name", session.agent_name or "未命名 Agent"))
        create_request = CreateAgentRequest(
            name=agent_name,
            description=str(config.get("description", "")),
            system_prompt=str(config.get("system_prompt", "")),
            model_id=str(config.get("model_id", "")),
            temperature=float(config.get("temperature", 0.7)),
            max_tokens=int(config.get("max_tokens", 4096)),
        )

        agent_info = await self._agent_creator.create_agent(create_request, user_id)
        session.confirm_creation(agent_info.id)
        updated = await self._session_repo.update(session)
        log.info("builder_session_confirmed", session_id=session_id, agent_id=agent_info.id)
        return BuilderSessionDTO.from_entity(updated)

    async def get_session(self, session_id: int, user_id: int) -> BuilderSessionDTO:
        """获取会话详情（校验所有权）。

        Raises:
            BuilderSessionNotFoundError: 会话不存在
            ForbiddenError: 无权操作
        """
        session = await self._get_owned_session(session_id, user_id)
        return BuilderSessionDTO.from_entity(session)

    async def cancel_session(self, session_id: int, user_id: int) -> BuilderSessionDTO:
        """取消会话。

        Raises:
            BuilderSessionNotFoundError: 会话不存在
            ForbiddenError: 无权操作
            InvalidStateTransitionError: 状态不允许取消
        """
        session = await self._get_owned_session(session_id, user_id)
        session.cancel()
        updated = await self._session_repo.update(session)
        log.info("builder_session_cancelled", session_id=session_id)
        return BuilderSessionDTO.from_entity(updated)

    # ── 内部辅助方法 ──

    async def _get_owned_session(self, session_id: int, user_id: int) -> BuilderSession:
        """获取会话并校验所有权。"""
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise BuilderSessionNotFoundError(session_id)
        check_ownership(session, user_id, owner_field="user_id", error_code="FORBIDDEN_BUILDER_SESSION")
        return session
