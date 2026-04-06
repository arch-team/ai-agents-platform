"""Builder 应用服务。"""

from collections.abc import AsyncIterator

import structlog

from src.modules.builder.application.blueprint_parser import parse_blueprint_output
from src.modules.builder.application.dto.builder_dto import BuilderSessionDTO, RefineBuilderDTO, TriggerBuilderDTO
from src.modules.builder.application.interfaces.builder_llm_service import (
    IBuilderLLMService,
    PlatformContext,
    PlatformSkillInfo,
    PlatformToolInfo,
)
from src.modules.builder.domain.entities.builder_session import BuilderSession
from src.modules.builder.domain.exceptions import BuilderSessionNotFoundError
from src.modules.builder.domain.repositories.builder_session_repository import IBuilderSessionRepository
from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.shared.application.ownership import check_ownership
from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.domain.interfaces.agent_creator import (
    BlueprintData,
    CreateAgentWithBlueprintRequest,
    CreatedAgentInfo,
    GuardrailData,
    IAgentCreator,
    PersonaData,
    ToolBindingData,
)
from src.shared.domain.interfaces.agent_lifecycle import IAgentLifecycle
from src.shared.domain.interfaces.skill_creator import CreateSkillRequest, ISkillCreator
from src.shared.domain.interfaces.skill_querier import ISkillQuerier, SkillSummary
from src.shared.domain.interfaces.tool_querier import ApprovedToolInfo, IToolQuerier


log = structlog.get_logger(__name__)


class BuilderService:
    """Builder 业务服务，编排 Agent Blueprint 生成和确认创建流程。

    多轮 SOP 引导 → Blueprint → Skill 创建 → workspace Agent 创建
    """

    def __init__(
        self,
        session_repo: IBuilderSessionRepository,
        llm_service: IBuilderLLMService,
        agent_creator: IAgentCreator,
        *,
        agent_lifecycle: IAgentLifecycle | None = None,
        skill_creator: ISkillCreator | None = None,
        tool_querier: IToolQuerier | None = None,
        skill_querier: ISkillQuerier | None = None,
    ) -> None:
        self._session_repo = session_repo
        self._llm_service = llm_service
        self._agent_creator = agent_creator
        self._agent_lifecycle = agent_lifecycle
        self._skill_creator = skill_creator
        self._tool_querier = tool_querier
        self._skill_querier = skill_querier

    async def create_session(self, dto: TriggerBuilderDTO, user_id: int) -> BuilderSessionDTO:
        """创建 Builder 会话（PENDING 状态）。"""
        session = BuilderSession(
            user_id=user_id,
            prompt=dto.prompt,
            template_id=dto.template_id,
            selected_skill_ids=dto.selected_skill_ids,
        )
        created = await self._session_repo.create(session)
        log.info("builder_session_created", session_id=created.id, user_id=user_id)
        return BuilderSessionDTO.from_entity(created)

    async def generate_blueprint_stream(self, session_id: int, user_id: int) -> AsyncIterator[str]:
        """SSE 流式生成 Agent Blueprint (SOP 引导式)。

        PENDING -> GENERATING -> CONFIRMED (成功)
        """
        session = await self._get_owned_session(session_id, user_id)
        session.start_generation()
        session.add_message("user", session.prompt)
        await self._session_repo.update(session)
        async for chunk in self._stream_and_parse_blueprint(session):
            yield chunk

    async def refine_session(
        self,
        session_id: int,
        user_id: int,
        *,
        dto: RefineBuilderDTO,
    ) -> AsyncIterator[str]:
        """多轮迭代 — 用户追加需求 → LLM 更新 Blueprint。

        CONFIRMED -> GENERATING -> CONFIRMED
        """
        session = await self._get_owned_session(session_id, user_id)
        session.start_refinement()
        session.add_message("user", dto.message)
        await self._session_repo.update(session)
        async for chunk in self._stream_and_parse_blueprint(session):
            yield chunk

    async def confirm_session(
        self,
        session_id: int,
        user_id: int,
        *,
        name_override: str | None = None,
        auto_start_testing: bool = False,
    ) -> BuilderSessionDTO:
        """确认会话并创建 Agent (Blueprint 模式)。

        CONFIRMED 状态 = LLM 已完成 Blueprint 生成，可以创建 Agent。
        auto_start_testing=True 时, 创建后自动触发 DRAFT -> TESTING。
        """
        session = await self._get_owned_session(session_id, user_id)

        if session.status != BuilderStatus.CONFIRMED:
            raise InvalidStateTransitionError(
                entity_type="BuilderSession",
                current_state=session.status.value,
                target_state="confirm_creation",
            )

        if not session.generated_blueprint:
            raise InvalidStateTransitionError(
                entity_type="BuilderSession",
                current_state=session.status.value,
                target_state="confirm_creation",
            )

        agent_info = await self._confirm_and_create_agent(session, user_id, name_override=name_override)

        # 可选触发 start_testing (通过 IAgentLifecycle)
        if auto_start_testing and self._agent_lifecycle:
            try:
                await self._agent_lifecycle.start_testing(agent_info.id, user_id)
                log.info("builder_auto_start_testing", agent_id=agent_info.id)
            except Exception:
                log.warning("builder_auto_start_testing_failed", agent_id=agent_info.id)

        session.confirm_creation(agent_info.id)
        updated = await self._session_repo.update(session)
        log.info("builder_session_confirmed", session_id=session_id, agent_id=agent_info.id)
        return BuilderSessionDTO.from_entity(updated)

    async def get_session(self, session_id: int, user_id: int) -> BuilderSessionDTO:
        """获取会话详情（校验所有权）。"""
        session = await self._get_owned_session(session_id, user_id)
        return BuilderSessionDTO.from_entity(session)

    async def cancel_session(self, session_id: int, user_id: int) -> BuilderSessionDTO:
        """取消会话。"""
        session = await self._get_owned_session(session_id, user_id)
        session.cancel()
        updated = await self._session_repo.update(session)
        log.info("builder_session_cancelled", session_id=session_id)
        return BuilderSessionDTO.from_entity(updated)

    # ── 平台能力查询 ──

    async def get_available_tools(self) -> list[ApprovedToolInfo]:
        """查询平台可用工具列表。"""
        if self._tool_querier is None:
            return []
        return await self._tool_querier.list_approved_tools()

    async def get_available_skills(self) -> list[SkillSummary]:
        """查询平台可用 Skill 列表。"""
        if self._skill_querier is None:
            return []
        return await self._skill_querier.list_published_skills()

    # ── 内部编排 ──

    async def _confirm_and_create_agent(
        self,
        session: BuilderSession,
        user_id: int,
        *,
        name_override: str | None = None,
    ) -> CreatedAgentInfo:
        """确认流程: Blueprint → Skills → Agent。"""
        bp = session.generated_blueprint
        assert bp is not None

        agent_name = name_override or session.agent_name or str(bp.get("persona", {}).get("role", "未命名 Agent"))

        # 1. 为每个 Skill 创建文件 + DB 记录
        skill_ids: list[int] = []
        skill_paths: list[str] = []
        if self._skill_creator and bp.get("skills"):
            for skill_data in bp["skills"]:
                # 构建 SKILL.md 内容
                skill_md = self._build_skill_md(skill_data)
                created = await self._skill_creator.create_skill(
                    CreateSkillRequest(
                        name=skill_data.get("name", "unnamed-skill"),
                        description=skill_data.get("trigger", ""),
                        skill_md=skill_md,
                        trigger_description=skill_data.get("trigger", ""),
                    ),
                    user_id,
                )
                published = await self._skill_creator.publish_skill(created.id, user_id)
                skill_ids.append(published.id)
                skill_paths.append(published.file_path)

        # 2. 构建 BlueprintData
        persona_data = bp.get("persona", {})
        tool_bindings_data = bp.get("tool_bindings", [])
        guardrails_data = bp.get("guardrails", [])

        blueprint_data = BlueprintData(
            persona=PersonaData(
                role=persona_data.get("role", ""),
                background=persona_data.get("background", ""),
                tone=persona_data.get("tone", ""),
            ),
            skill_ids=tuple(skill_ids),
            skill_paths=tuple(skill_paths),
            tool_bindings=tuple(
                ToolBindingData(
                    tool_id=t.get("tool_id", 0),
                    display_name=t.get("display_name", ""),
                    usage_hint=t.get("usage_hint", ""),
                )
                for t in tool_bindings_data
            ),
            guardrails=tuple(
                GuardrailData(rule=g.get("rule", ""), severity=g.get("severity", "warn")) for g in guardrails_data
            ),
        )

        # 3. 创建 Agent with Blueprint (agents 模块负责 workspace + DB)
        return await self._agent_creator.create_agent_with_blueprint(
            CreateAgentWithBlueprintRequest(name=agent_name, blueprint=blueprint_data),
            user_id,
        )

    # ── 内部辅助方法 ──

    async def _stream_and_parse_blueprint(self, session: BuilderSession) -> AsyncIterator[str]:
        """共享: LLM 流式生成 + Blueprint 解析 + 持久化。"""
        from src.modules.builder.application.interfaces.builder_llm_service import BuilderMessage

        platform_context = await self._build_platform_context()
        messages = [BuilderMessage(role=m["role"], content=m["content"]) for m in session.messages]

        chunks: list[str] = []
        async for chunk in self._llm_service.generate_blueprint(messages, platform_context):
            chunks.append(chunk)
            yield chunk

        full_text = "".join(chunks).strip()
        self._try_parse_and_save_blueprint(session, full_text)
        await self._session_repo.update(session)

    async def _get_owned_session(self, session_id: int, user_id: int) -> BuilderSession:
        """获取会话并校验所有权。"""
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise BuilderSessionNotFoundError(session_id)
        check_ownership(session, user_id, owner_field="user_id", error_code="FORBIDDEN_BUILDER_SESSION")
        return session

    async def _build_platform_context(self) -> PlatformContext:
        """构建 LLM 平台上下文。"""
        tools: tuple[PlatformToolInfo, ...] = ()
        skills: tuple[PlatformSkillInfo, ...] = ()

        if self._tool_querier:
            approved = await self._tool_querier.list_approved_tools()
            tools = tuple(PlatformToolInfo(id=t.id, name=t.name, description=t.description) for t in approved)

        if self._skill_querier:
            published = await self._skill_querier.list_published_skills()
            skills = tuple(
                PlatformSkillInfo(id=s.id, name=s.name, description=s.description, category=s.category)
                for s in published
            )

        return PlatformContext(available_tools=tools, available_skills=skills)

    def _try_parse_and_save_blueprint(self, session: BuilderSession, full_text: str) -> None:
        """尝试从 LLM 输出解析 Blueprint 并保存到 session。"""
        parsed = parse_blueprint_output(full_text)
        blueprint_dict: dict[str, object] = {}

        if parsed.persona:
            blueprint_dict["persona"] = {
                "role": parsed.persona.role,
                "background": parsed.persona.background,
                "tone": parsed.persona.tone,
            }
        if parsed.skills:
            blueprint_dict["skills"] = [
                {"name": s.name, "trigger": s.trigger, "steps": list(s.steps), "rules": list(s.rules)}
                for s in parsed.skills
            ]
        if parsed.tool_bindings:
            blueprint_dict["tool_bindings"] = [
                {"tool_id": t.tool_id, "display_name": t.display_name, "usage_hint": t.usage_hint}
                for t in parsed.tool_bindings
            ]
        if parsed.guardrails:
            blueprint_dict["guardrails"] = [{"rule": g.rule, "severity": g.severity} for g in parsed.guardrails]

        if blueprint_dict:
            name = ""
            if parsed.persona:
                name = parsed.persona.role
            session.complete_generation(config={}, name=name or "未命名 Agent", blueprint=blueprint_dict)
            session.add_message("assistant", full_text)
            log.info("builder_blueprint_parsed", session_id=session.id, sections=list(blueprint_dict.keys()))
        else:
            # 没有结构化段: 引导性对话, 仍需转为 CONFIRMED 以允许后续 refine (BUG-3)
            session.add_message("assistant", full_text)
            session.complete_generation(
                config=session.generated_config or {},
                name=session.agent_name or "未命名 Agent",
                blueprint=session.generated_blueprint,
            )
            log.info("builder_no_blueprint_sections", session_id=session.id)

    @staticmethod
    def _build_skill_md(skill_data: dict[str, object]) -> str:
        """从 Blueprint 中的 skill 数据构建 SKILL.md 内容。"""
        lines: list[str] = [
            "---",
            f"name: {skill_data.get('name', '')}",
            f"description: {skill_data.get('trigger', '')}",
            "---",
            "",
            f"# {skill_data.get('name', '')}",
            "",
        ]

        trigger = skill_data.get("trigger", "")
        if trigger:
            lines.append(f"**触发条件**: {trigger}")
            lines.append("")

        steps = skill_data.get("steps", [])
        if isinstance(steps, list) and steps:
            lines.append("## 操作步骤")
            lines.extend(str(step) for step in steps)
            lines.append("")

        rules = skill_data.get("rules", [])
        if isinstance(rules, list) and rules:
            lines.append("## 业务规则")
            lines.extend(f"- {rule}" for rule in rules)
            lines.append("")

        return "\n".join(lines)
