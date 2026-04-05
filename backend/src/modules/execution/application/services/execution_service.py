"""Execution 应用服务。"""

import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from typing import Any

import structlog
from opentelemetry import trace

from src.modules.execution.application.dto.execution_dto import (
    ContextWindowConfig,
    ConversationDetailDTO,
    ConversationDTO,
    CreateConversationDTO,
    MessageDTO,
    SendMessageDTO,
    StreamChunk,
)
from src.modules.execution.application.interfaces.agent_runtime import (
    AgentRequest,
    AgentResponseChunk,
    AgentTool,
    IAgentRuntime,
)
from src.modules.execution.application.interfaces.gateway_auth import IGatewayAuthService
from src.modules.execution.application.interfaces.llm_client import (
    ILLMClient,
    LLMMessage,
    LLMStreamChunk,
)
from src.modules.execution.application.interfaces.memory_service import IMemoryService
from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.entities.message import Message
from src.modules.execution.domain.events import (
    ConversationCompletedEvent,
    ConversationCreatedEvent,
    MessageReceivedEvent,
    MessageSentEvent,
)
from src.modules.execution.domain.exceptions import (
    AgentNotAvailableError,
    ConversationNotActiveError,
    ConversationNotFoundError,
)
from src.modules.execution.domain.repositories.conversation_repository import (
    IConversationRepository,
)
from src.modules.execution.domain.repositories.message_repository import (
    IMessageRepository,
)
from src.modules.execution.domain.value_objects.conversation_status import (
    ConversationStatus,
)
from src.modules.execution.domain.value_objects.message_role import MessageRole
from src.shared.application.dtos import PagedResult
from src.shared.application.ownership import check_ownership, get_or_raise
from src.shared.domain.event_bus import event_bus
from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo, IAgentQuerier
from src.shared.domain.interfaces.knowledge_querier import IKnowledgeQuerier
from src.shared.domain.interfaces.tool_querier import ApprovedToolInfo, IToolQuerier


@dataclass
class _SendContext:
    """send_message / send_message_stream 共享的前置准备结果。"""

    conversation: Conversation
    agent_info: ActiveAgentInfo
    created_user_msg: Message
    llm_messages: list[LLMMessage]
    system_prompt: str = ""


# 异步无参回调类型 (用于 stream session 生命周期管理)
AsyncCallback = Callable[[], Coroutine[Any, Any, None]]

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)

# token 估算: 英文约 4 字符/token, 中文约 1.5 字符/token
# 使用 2 作为中英混合保守值, 避免上下文窗口溢出
_CHARS_PER_TOKEN = 2


class ExecutionService:
    """Execution 业务服务，编排对话和消息的用例。"""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        message_repo: IMessageRepository,
        llm_client: ILLMClient,
        agent_querier: IAgentQuerier,
        stream_finalize_repos: tuple[IMessageRepository, IConversationRepository] | None = None,
        knowledge_querier: IKnowledgeQuerier | None = None,
        agent_runtime: IAgentRuntime | None = None,
        tool_querier: IToolQuerier | None = None,
        gateway_url: str = "",
        context_window: ContextWindowConfig | None = None,
        stream_session_commit: AsyncCallback | None = None,
        stream_session_close: AsyncCallback | None = None,
        gateway_auth: IGatewayAuthService | None = None,
        memory_adapter: IMemoryService | None = None,
        memory_id: str = "",
        local_agent_runtime: IAgentRuntime | None = None,
        stats_repo_factory: Callable[
            [],
            tuple[
                IConversationRepository,
                Callable[[], Coroutine[Any, Any, None]],
                Callable[[], Coroutine[Any, Any, None]],
            ],
        ]
        | None = None,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._llm_client = llm_client
        self._agent_querier = agent_querier
        self._knowledge_querier = knowledge_querier
        self._agent_runtime = agent_runtime
        self._local_agent_runtime = local_agent_runtime
        self._tool_querier = tool_querier
        self._gateway_url = gateway_url
        self._gateway_auth = gateway_auth
        self._memory_adapter = memory_adapter
        self._memory_id = memory_id
        self._context_window = context_window or ContextWindowConfig()
        self._stream_session_commit = stream_session_commit
        self._stream_session_close = stream_session_close
        self._stats_repo_factory = stats_repo_factory
        # 流后 DB 写使用独立 repos (由 API 层通过独立 session 创建)
        self._stream_msg_repo, self._stream_conv_repo = stream_finalize_repos or (message_repo, conversation_repo)

    async def create_conversation(
        self,
        dto: CreateConversationDTO,
        user_id: int,
    ) -> ConversationDTO:
        """创建对话。校验 Agent ACTIVE 状态。发布 ConversationCreatedEvent。

        Raises:
            AgentNotAvailableError: Agent 不存在或非 ACTIVE
        """
        agent_info = await self._agent_querier.get_executable_agent(dto.agent_id)
        if agent_info is None:
            raise AgentNotAvailableError(dto.agent_id)

        title = dto.title or f"与 {agent_info.name} 的对话"

        conversation = Conversation(
            title=title,
            agent_id=dto.agent_id,
            user_id=user_id,
        )
        created = await self._conversation_repo.create(conversation)
        if created.id is None:
            msg = "Conversation 创建后 ID 不能为空"
            raise ValueError(msg)

        await event_bus.publish_async(
            ConversationCreatedEvent(
                conversation_id=created.id,
                agent_id=dto.agent_id,
                user_id=user_id,
            ),
        )
        return self._to_conversation_dto(created)

    async def send_message(
        self,
        conversation_id: int,
        dto: SendMessageDTO,
        user_id: int,
    ) -> MessageDTO:
        """发送消息（同步）。

        根据 runtime_type 路由:
        - "agent" 且 agent_runtime 可用 → IAgentRuntime.execute()
        - 其他情况 → ILLMClient.invoke()（降级路径）

        Raises:
            ConversationNotFoundError, ConversationNotActiveError,
            DomainError(FORBIDDEN_CONVERSATION), AgentNotAvailableError
        """
        ctx = await self._prepare_for_send(conversation_id, dto.content, user_id)

        # 根据 runtime_type 路由执行
        if self._should_use_agent_runtime(ctx.agent_info):
            response_content, total_tokens = await self._execute_agent(ctx)
        else:
            response_content, total_tokens = await self._execute_llm(ctx)

        # 创建助手消息
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response_content,
            token_count=total_tokens,
        )
        created_assistant_msg = await self._message_repo.create(assistant_message)

        # 更新对话统计 (同步路径: DI session 内一次性更新, 无死锁风险)
        ctx.conversation.add_message_count(token_count=0)  # 用户消息
        ctx.conversation.add_message_count(token_count=total_tokens)  # 助手消息
        await self._conversation_repo.update(ctx.conversation)

        if ctx.created_user_msg.id is None or created_assistant_msg.id is None:
            msg = "消息 ID 不能为空"
            raise ValueError(msg)
        await self._publish_message_events(
            conversation_id=conversation_id,
            user_msg_id=ctx.created_user_msg.id,
            assistant_msg_id=created_assistant_msg.id,
            total_tokens=total_tokens,
            model_id=ctx.agent_info.model_id,
            user_id=user_id,
        )

        return self._to_message_dto(created_assistant_msg)

    async def send_message_stream(
        self,
        conversation_id: int,
        dto: SendMessageDTO,
        user_id: int,
    ) -> AsyncIterator[StreamChunk]:
        """发送消息（流式），yield 结构化 StreamChunk 由 API 层转换为 SSE 事件。

        根据 runtime_type 路由:
        - "agent" 且 agent_runtime 可用 → IAgentRuntime.execute_stream()
        - 其他情况 → ILLMClient.invoke_stream()（降级路径）

        Raises:
            ConversationNotFoundError, ConversationNotActiveError,
            DomainError(FORBIDDEN_CONVERSATION), AgentNotAvailableError
        """
        ctx = await self._prepare_for_send(conversation_id, dto.content, user_id)

        # 创建空助手消息占位 (使用 stream_session, 确保后续 _finalize_stream 能在同一 session 中更新)
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="",
        )
        created_assistant_msg = await self._stream_msg_repo.create(assistant_message)

        use_agent = self._should_use_agent_runtime(ctx.agent_info)

        async def _generate() -> AsyncIterator[StreamChunk]:
            collected_content = ""
            total_input_tokens = 0
            total_output_tokens = 0

            try:
                # 根据 runtime_type 路由到对应的流式迭代器 (需 await 协程获取迭代器)
                source = await self._create_agent_stream(ctx) if use_agent else await self._create_llm_stream(ctx)
                async for chunk in source:
                    if chunk.content:
                        collected_content += chunk.content
                        yield StreamChunk(content=chunk.content)
                    if chunk.done:
                        total_input_tokens = chunk.input_tokens
                        total_output_tokens = chunk.output_tokens
            except Exception:
                await self._compensate_user_message_count(  # 异常补偿
                    conversation_id,
                    created_assistant_msg,
                )
                raise

            # 流后 DB 写操作: 使用独立 session, 避免 DI session 已关闭的问题
            total_tokens = total_input_tokens + total_output_tokens
            await self._finalize_stream(
                conversation_id=conversation_id,
                user_msg=ctx.created_user_msg,
                assistant_msg=created_assistant_msg,
                collected_content=collected_content,
                total_tokens=total_tokens,
                model_id=ctx.agent_info.model_id,
                user_id=user_id,
            )

            yield StreamChunk(
                done=True,
                message_id=created_assistant_msg.id,
                token_count=total_tokens,
            )

        return _generate()

    async def _finalize_stream(
        self,
        *,
        conversation_id: int,
        user_msg: Message,
        assistant_msg: Message,
        collected_content: str,
        total_tokens: int,
        model_id: str,
        user_id: int,
    ) -> None:
        """流式传输完成后的 DB 写操作和事件发布。

        1. stream_session: 仅更新助手消息内容 → commit → close
        2. 独立短事务: 原子增量更新 conversation 统计 (避免行锁竞争)
        3. 事件发布: 不依赖 DB session
        """
        if user_msg.id is None or assistant_msg.id is None:
            msg = "消息 ID 不能为空"
            raise ValueError(msg)

        try:
            # Step 1: stream_session 只更新助手消息 (不触碰 conversations 表)
            assistant_msg.content = collected_content
            assistant_msg.token_count = total_tokens
            await self._stream_msg_repo.update(assistant_msg)

            if self._stream_session_commit:
                await self._stream_session_commit()
        except Exception:
            logger.exception("stream_finalize_failed", conversation_id=conversation_id)
            raise
        finally:
            if self._stream_session_close:
                await self._stream_session_close()

        # Step 2: 独立短事务更新 conversation 统计 (原子增量, 不持有长锁)
        # best-effort: 统计更新失败不影响消息已保存的事实
        await self._increment_conversation_stats(conversation_id, message_delta=2, token_delta=total_tokens)

        # Step 3: 发布事件
        await self._publish_message_events(
            conversation_id=conversation_id,
            user_msg_id=user_msg.id,
            assistant_msg_id=assistant_msg.id,
            total_tokens=total_tokens,
            model_id=model_id,
            user_id=user_id,
        )

    async def _increment_conversation_stats(
        self,
        conversation_id: int,
        *,
        message_delta: int,
        token_delta: int,
    ) -> None:
        """独立短事务更新 conversation 统计 (原子增量)。

        通过 stats_repo_factory 创建一次性 session + repo, 避免与 DI / stream session 竞争行锁。
        best-effort: 失败仅记录警告, 不影响已保存的消息。
        """
        if self._stats_repo_factory is None:
            logger.warning("stats_repo_factory_not_configured", conversation_id=conversation_id)
            return
        try:
            repo, commit, close = self._stats_repo_factory()
            try:
                await repo.increment_message_stats(
                    conversation_id,
                    message_delta=message_delta,
                    token_delta=token_delta,
                )
                await commit()
            finally:
                await close()
        except Exception:
            logger.warning("increment_conversation_stats_failed", conversation_id=conversation_id)

    async def _compensate_user_message_count(
        self,
        conversation_id: int,
        assistant_msg: Message | None = None,
    ) -> None:
        """流失败时补偿: 更新用户消息计数 + 清理助手消息占位。

        使用独立短事务原子增量, 与 _increment_conversation_stats 一致。
        best-effort: 补偿失败不阻塞异常传播。

        资源管理: 异常路径调用 close 后置 None, 防止 _finalize_stream 二次关闭。
        (实际上两条路径互斥, 但置 None 是防御性保障)
        """
        await self._increment_conversation_stats(conversation_id, message_delta=1, token_delta=0)
        # 清理未完成的助手消息占位记录
        if assistant_msg is not None and assistant_msg.id is not None:
            try:
                await self._stream_msg_repo.delete(assistant_msg.id)
            except Exception:
                logger.warning("cleanup_assistant_placeholder_failed", conversation_id=conversation_id)
        # 关闭 stream_session (助手消息占位通过事务回滚清除)
        if self._stream_session_close:
            await self._stream_session_close()
            self._stream_session_close = None

    async def get_conversation(
        self,
        conversation_id: int,
        user_id: int,
    ) -> ConversationDetailDTO:
        """获取对话详情（含消息历史）。校验所有权。

        Raises:
            ConversationNotFoundError, DomainError(FORBIDDEN_CONVERSATION)
        """
        conversation = await self._get_conversation_or_raise(conversation_id)
        self._check_ownership(conversation, user_id)

        messages = await self._message_repo.list_by_conversation(conversation_id)
        return ConversationDetailDTO(
            conversation=self._to_conversation_dto(conversation),
            messages=[self._to_message_dto(m) for m in messages],
        )

    async def list_conversations(
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[ConversationDTO]:
        """获取对话列表。"""
        offset = (page - 1) * page_size

        conversations = await self._conversation_repo.list_by_user(
            user_id,
            agent_id=agent_id,
            offset=offset,
            limit=page_size,
        )
        total = await self._conversation_repo.count_by_user(
            user_id,
            agent_id=agent_id,
        )

        return PagedResult(
            items=[self._to_conversation_dto(c) for c in conversations],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def complete_conversation(
        self,
        conversation_id: int,
        user_id: int,
    ) -> ConversationDTO:
        """结束对话。校验所有权。发布 ConversationCompletedEvent。

        Raises:
            ConversationNotFoundError, DomainError(FORBIDDEN_CONVERSATION),
            InvalidStateTransitionError
        """
        conversation = await self._get_conversation_or_raise(conversation_id)
        self._check_ownership(conversation, user_id)

        conversation.complete()
        updated = await self._conversation_repo.update(conversation)

        await event_bus.publish_async(
            ConversationCompletedEvent(
                conversation_id=conversation_id,
                user_id=user_id,
            ),
        )
        return self._to_conversation_dto(updated)

    # ── 内部辅助方法 ──

    @staticmethod
    async def _publish_message_events(
        *,
        conversation_id: int,
        user_msg_id: int,
        assistant_msg_id: int,
        total_tokens: int,
        model_id: str,
        user_id: int,
    ) -> None:
        """并行发布消息发送和接收事件 (send_message 和 _finalize_stream 共用)。"""
        await asyncio.gather(
            event_bus.publish_async(
                MessageSentEvent(conversation_id=conversation_id, message_id=user_msg_id, user_id=user_id),
            ),
            event_bus.publish_async(
                MessageReceivedEvent(
                    conversation_id=conversation_id,
                    message_id=assistant_msg_id,
                    token_count=total_tokens,
                    model_id=model_id,
                ),
            ),
        )

    def _should_use_agent_runtime(self, agent_info: ActiveAgentInfo) -> bool:
        """判断是否使用 Agent 运行时路径。

        三模式路由: 主 runtime 或 local runtime 有一个可用即走 Agent 路径。
        """
        if agent_info.runtime_type != "agent":
            return False
        if self._agent_runtime is not None:
            return True
        # 模式2 降级: 主 runtime 不可用但 local runtime 可用 (DRAFT + workspace_path)
        return agent_info.workspace_path != "" and self._local_agent_runtime is not None

    def _select_runtime(self, ctx: _SendContext) -> IAgentRuntime:
        """根据三模式路由选择 runtime: 模式2 优先 local, 其他用 main。"""
        # 模式2: 本地 cwd — 优先使用 local_agent_runtime
        if ctx.agent_info.workspace_path and not ctx.agent_info.runtime_arn and self._local_agent_runtime is not None:
            return self._local_agent_runtime
        if self._agent_runtime is None:
            msg = "Agent runtime 未配置"
            raise ValueError(msg)
        return self._agent_runtime

    async def _execute_agent(self, ctx: _SendContext) -> tuple[str, int]:
        """通过 IAgentRuntime 执行（Agent 模式）。返回 (content, total_tokens)。"""
        runtime = self._select_runtime(ctx)
        with tracer.start_as_current_span(
            "agent.execute",
            attributes={
                "agent.id": str(ctx.agent_info.id),
                "agent.type": ctx.agent_info.runtime_type,
                "agent.model_id": ctx.agent_info.model_id,
            },
        ):
            tools = await self._get_agent_tools(ctx.agent_info.id)
            gateway_auth_token = await self._get_gateway_auth_token(tools)
            request = self._build_agent_request(ctx, tools, gateway_auth_token=gateway_auth_token)
            response = await runtime.execute(request)
            total_tokens = response.input_tokens + response.output_tokens
            return response.content, total_tokens

    async def _execute_llm(self, ctx: _SendContext) -> tuple[str, int]:
        """通过 ILLMClient 执行（降级路径）。返回 (content, total_tokens)。"""
        with tracer.start_as_current_span(
            "llm.invoke",
            attributes={
                "llm.model_id": ctx.agent_info.model_id,
                "llm.max_tokens": ctx.agent_info.max_tokens,
            },
        ):
            response = await self._llm_client.invoke(
                model_id=ctx.agent_info.model_id,
                messages=ctx.llm_messages,
                system_prompt=ctx.system_prompt,
                temperature=ctx.agent_info.temperature,
                max_tokens=ctx.agent_info.max_tokens,
                top_p=ctx.agent_info.top_p,
                stop_sequences=ctx.agent_info.stop_sequences,
            )
            total_tokens = response.input_tokens + response.output_tokens
            return response.content, total_tokens

    async def _create_agent_stream(self, ctx: _SendContext) -> AsyncIterator[AgentResponseChunk]:
        """创建 Agent 路径的流式迭代器。"""
        runtime = self._select_runtime(ctx)
        tools = await self._get_agent_tools(ctx.agent_info.id)
        gateway_auth_token = await self._get_gateway_auth_token(tools)
        request = self._build_agent_request(ctx, tools, gateway_auth_token=gateway_auth_token)
        return await runtime.execute_stream(request)

    async def _create_llm_stream(self, ctx: _SendContext) -> AsyncIterator[LLMStreamChunk]:
        """创建 LLM 降级路径的流式迭代器。"""
        return await self._llm_client.invoke_stream(
            model_id=ctx.agent_info.model_id,
            messages=ctx.llm_messages,
            system_prompt=ctx.system_prompt,
            temperature=ctx.agent_info.temperature,
            max_tokens=ctx.agent_info.max_tokens,
            top_p=ctx.agent_info.top_p,
            stop_sequences=ctx.agent_info.stop_sequences,
        )

    async def _get_agent_tools(self, agent_id: int) -> list[AgentTool]:
        """获取指定 Agent 绑定的工具并转换为 AgentTool。

        使用 list_tools_for_agent(agent_id) 按 Agent 绑定关系过滤，
        而非 list_approved_tools() 返回全平台工具。
        降级: IToolQuerier 异常时返回空列表, Agent 无工具继续执行。
        """
        if self._tool_querier is None:
            return []
        with tracer.start_as_current_span("tools.load"):
            try:
                approved = await self._tool_querier.list_tools_for_agent(agent_id)
            except Exception:
                logger.warning("tool_querier_degraded", reason="list_tools_for_agent failed", agent_id=agent_id)
                return []
            tools = [self._to_agent_tool(t) for t in approved]
            span = trace.get_current_span()
            span.set_attribute("tools.count", len(tools))
            span.set_attribute("agent.id", agent_id)
            return tools

    _TOOL_CONFIG_FIELDS: tuple[str, ...] = (
        "server_url",
        "transport",
        "endpoint_url",
        "method",
        "runtime",
        "handler",
    )

    @staticmethod
    def _to_agent_tool(info: ApprovedToolInfo) -> AgentTool:
        """ApprovedToolInfo → AgentTool 转换。"""
        # 收集非空配置字段
        config: dict[str, str] = {k: v for k in ExecutionService._TOOL_CONFIG_FIELDS if (v := getattr(info, k))}
        if info.auth_type != "none":
            config["auth_type"] = info.auth_type
        return AgentTool(
            name=info.name,
            description=info.description,
            input_schema={},
            tool_type=info.tool_type,
            config=config,
        )

    async def _get_gateway_auth_token(self, tools: list[AgentTool]) -> str:
        """获取 Gateway 认证 Token（仅当存在 mcp_server 工具且 gateway_auth 已配置时）。"""
        if self._gateway_auth is None:
            return ""
        has_mcp_tools = any(t.tool_type == "mcp_server" for t in tools)
        if not has_mcp_tools:
            return ""
        return await self._gateway_auth.get_bearer_token()

    def _build_agent_request(
        self,
        ctx: _SendContext,
        tools: list[AgentTool],
        *,
        gateway_auth_token: str = "",
    ) -> AgentRequest:
        """构建 AgentRequest — 二模式路由 (V1 兼容模式已移除)。

        模式1: runtime_arn → 专属 Runtime 容器, cwd="/workspace"
        模式2: workspace_path → 本地 cwd, CLAUDE.md 提供指令
        """
        cwd = ""
        runtime_arn = ""

        if ctx.agent_info.runtime_arn:
            # 模式1: 专属 Runtime
            runtime_arn = ctx.agent_info.runtime_arn
            cwd = "/workspace"
        elif ctx.agent_info.workspace_path:
            # 模式2: 本地 cwd
            cwd = ctx.agent_info.workspace_path

        return AgentRequest(
            prompt=ctx.created_user_msg.content,
            system_prompt="",
            model_id=ctx.agent_info.model_id,
            tools=tools,
            history=ctx.llm_messages,
            temperature=ctx.agent_info.temperature,
            max_tokens=ctx.agent_info.max_tokens,
            gateway_url=self._gateway_url,
            gateway_auth_token=gateway_auth_token,
            enable_teams=ctx.agent_info.enable_teams,
            memory_id=self._memory_id if ctx.agent_info.enable_memory else "",
            cwd=cwd,
            runtime_arn=runtime_arn,
        )

    async def _prepare_for_send(
        self,
        conversation_id: int,
        content: str,
        user_id: int,
    ) -> _SendContext:
        """send_message / send_message_stream 共有的前置逻辑。

        校验对话存在、所有权、活跃状态；校验 Agent 可用；
        创建用户消息；加载历史并构建 LLM 上下文。
        """
        conversation = await self._get_conversation_or_raise(conversation_id)
        self._check_ownership(conversation, user_id)
        self._check_active(conversation)

        agent_info = await self._agent_querier.get_executable_agent(conversation.agent_id)
        if agent_info is None:
            raise AgentNotAvailableError(conversation.agent_id)

        # 创建用户消息 (message_count 在 _finalize_stream 中统一更新,
        # 流失败时由 _generate 异常处理路径通过 stream_session 补偿更新)
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )
        created_user_msg = await self._message_repo.create(user_message)

        # 加载消息历史 → 滑动窗口截取 → 构建 LLM 上下文
        history = await self._message_repo.list_by_conversation(conversation_id)
        truncated = self._truncate_messages(history, max_tokens=self._context_window.max_message_tokens)
        llm_messages = [LLMMessage(role=m.role.value, content=m.content) for m in truncated]

        # RAG + Memory 并行检索: 两者互不依赖, 使用 asyncio.gather 并行执行
        # 降级: 任一检索异常时跳过注入, 不阻塞对话
        system_prompt = agent_info.system_prompt

        async def _retrieve_rag() -> list[Any]:
            if not (agent_info.knowledge_base_id and self._knowledge_querier):
                return []
            with tracer.start_as_current_span(
                "rag.retrieve",
                attributes={"rag.knowledge_base_id": str(agent_info.knowledge_base_id), "rag.top_k": 5},
            ):
                try:
                    return await self._knowledge_querier.retrieve(agent_info.knowledge_base_id, content, top_k=5)
                except Exception:
                    logger.warning("knowledge_querier_degraded", knowledge_base_id=agent_info.knowledge_base_id)
                    return []

        async def _recall_memory() -> tuple[list[Any], bool]:
            """检索 Memory, 返回 (结果列表, 是否降级)。"""
            if not (agent_info.enable_memory and self._memory_adapter is not None):
                return [], False
            with tracer.start_as_current_span(
                "memory.recall",
                attributes={"memory.agent_id": str(agent_info.id), "memory.top_k": 5},
            ):
                try:
                    results = await self._memory_adapter.recall_memory(agent_info.id, content, max_results=5)
                except Exception:
                    logger.exception("memory_recall_failed", agent_id=agent_info.id)
                    return [], True
                else:
                    return results, False

        rag_results, (memories, memory_degraded) = await asyncio.gather(_retrieve_rag(), _recall_memory())

        if rag_results:
            rag_context = "\n\n".join(f"[参考文档] {r.content}" for r in rag_results)
            system_prompt = f"{system_prompt}\n\n## 知识库参考资料\n\n{rag_context}"
        if memories:
            memory_context = "\n\n".join(f"[长期记忆 - {m.topic}] {m.content}" for m in memories)
            system_prompt = f"{system_prompt}\n\n## 长期记忆\n\n{memory_context}"
            logger.info("memory_injected", agent_id=agent_info.id, memory_count=len(memories))
        if memory_degraded:
            system_prompt = f"{system_prompt}\n\n[Memory 服务暂时不可用, 请告知用户]"

        return _SendContext(
            conversation=conversation,
            agent_info=agent_info,
            created_user_msg=created_user_msg,
            llm_messages=llm_messages,
            system_prompt=system_prompt,
        )

    async def _get_conversation_or_raise(
        self,
        conversation_id: int,
    ) -> Conversation:
        return await get_or_raise(
            self._conversation_repo,
            conversation_id,
            ConversationNotFoundError,
            conversation_id,
        )

    @staticmethod
    def _check_ownership(conversation: Conversation, user_id: int) -> None:
        """校验对话所有权。"""
        check_ownership(conversation, user_id, owner_field="user_id", error_code="FORBIDDEN_CONVERSATION")

    @staticmethod
    def _check_active(conversation: Conversation) -> None:
        """校验对话处于活跃状态。"""
        if conversation.status != ConversationStatus.ACTIVE:
            if conversation.id is None:
                msg = "Conversation ID 不能为空"
                raise ValueError(msg)
            raise ConversationNotActiveError(conversation.id)

    @staticmethod
    def _to_conversation_dto(conv: Conversation) -> ConversationDTO:
        id_, created_at, updated_at = conv.require_persisted()
        return ConversationDTO(
            id=id_,
            title=conv.title,
            agent_id=conv.agent_id,
            user_id=conv.user_id,
            status=conv.status.value,
            message_count=conv.message_count,
            total_tokens=conv.total_tokens,
            created_at=created_at,
            updated_at=updated_at,
        )

    @staticmethod
    def _estimate_tokens(msg: Message) -> int:
        """估算消息 token 数: 有实际值用实际值, 否则按字符估算。"""
        return msg.token_count if msg.token_count > 0 else max(len(msg.content) // _CHARS_PER_TOKEN, 1)

    @staticmethod
    def _truncate_messages(messages: list[Message], *, max_tokens: int) -> list[Message]:
        """从最新消息向前截取, 保持总 token 数在预算内。

        保留策略:
        1. 始终保留最早 1 条消息 (首条用户提问, 提供对话起点上下文)
        2. 剩余 token 窗口从最新消息向前填充
        3. 最终合并: 保留消息 + 最新对话消息 (按时间正序)

        token_count > 0 时使用实际值, 否则按 ~2 字符/token 估算。
        """
        if not messages:
            return []

        # 快速路径 - 全部在预算内
        total_est = sum(ExecutionService._estimate_tokens(m) for m in messages)
        if total_est <= max_tokens:
            return messages

        # 始终保留最早 1 条消息(系统指令)
        preserved = [messages[0]]
        remaining = messages[1:]

        # 计算保留消息占用的 token
        preserved_tokens = ExecutionService._estimate_tokens(preserved[0])
        available_tokens = max_tokens - preserved_tokens

        if available_tokens <= 0:
            return preserved

        # 从最新消息向前填充剩余窗口
        selected: list[Message] = []
        accumulated = 0

        for msg in reversed(remaining):
            est = ExecutionService._estimate_tokens(msg)
            if accumulated + est > available_tokens:
                break
            accumulated += est
            selected.append(msg)

        selected.reverse()

        # 合并并按时间正序返回
        all_selected = preserved + selected
        all_selected.sort(key=lambda m: m.id or 0)
        return all_selected

    @staticmethod
    def _to_message_dto(msg: Message) -> MessageDTO:
        if msg.id is None or msg.created_at is None:
            err = "Message 缺少必要字段 (id/created_at)"
            raise ValueError(err)
        return MessageDTO(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role.value,
            content=msg.content,
            token_count=msg.token_count,
            created_at=msg.created_at,
        )
