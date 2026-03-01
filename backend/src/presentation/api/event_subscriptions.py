"""事件订阅注册 — 将各模块 DomainEvent 绑定到对应的处理器。"""

from __future__ import annotations

from src.shared.infrastructure.settings import get_settings


def _register_audit_event_subscriptions() -> None:
    """注册审计事件订阅 — 将各模块 DomainEvent 自动记录为 AuditLog。

    订阅 agents/execution/tool_catalog/knowledge/templates 模块事件，
    通过 AuditEventSubscriber 统一转换为审计记录。
    """
    from src.modules.agents.domain.events import (
        AgentActivatedEvent,
        AgentArchivedEvent,
        AgentCreatedEvent,
        AgentDeletedEvent,
        AgentUpdatedEvent,
    )
    from src.modules.audit.application.services.audit_service import AuditService
    from src.modules.audit.infrastructure.event_subscriber import AuditEventSubscriber
    from src.modules.audit.infrastructure.persistence.repositories.audit_log_repository_impl import (
        AuditLogRepositoryImpl,
    )
    from src.modules.execution.domain.events import (
        ConversationCreatedEvent,
        TeamExecutionCompletedEvent,
        TeamExecutionFailedEvent,
        TeamExecutionStartedEvent,
    )
    from src.modules.knowledge.domain.events import (
        DocumentUploadedEvent,
        KnowledgeBaseActivatedEvent,
        KnowledgeBaseCreatedEvent,
        KnowledgeBaseDeletedEvent,
    )
    from src.modules.templates.domain.events import (
        TemplateArchivedEvent,
        TemplateCreatedEvent,
        TemplatePublishedEvent,
    )
    from src.modules.tool_catalog.domain.events import (
        ToolApprovedEvent as ToolApprovedAudit,
    )
    from src.modules.tool_catalog.domain.events import (
        ToolCreatedEvent,
        ToolDeletedEvent,
        ToolRejectedEvent,
        ToolSubmittedEvent,
        ToolUpdatedEvent,
    )
    from src.modules.tool_catalog.domain.events import (
        ToolDeprecatedEvent as ToolDeprecatedAudit,
    )
    from src.shared.domain.event_bus import event_bus
    from src.shared.infrastructure.database import get_session_factory

    session_factory = get_session_factory()

    # 需要订阅的所有事件类型
    event_types = [
        # agents
        AgentCreatedEvent,
        AgentUpdatedEvent,
        AgentActivatedEvent,
        AgentArchivedEvent,
        AgentDeletedEvent,
        # execution
        ConversationCreatedEvent,
        TeamExecutionStartedEvent,
        TeamExecutionCompletedEvent,
        TeamExecutionFailedEvent,
        # tool_catalog
        ToolCreatedEvent,
        ToolUpdatedEvent,
        ToolDeletedEvent,
        ToolSubmittedEvent,
        ToolApprovedAudit,
        ToolRejectedEvent,
        ToolDeprecatedAudit,
        # knowledge
        KnowledgeBaseCreatedEvent,
        KnowledgeBaseActivatedEvent,
        KnowledgeBaseDeletedEvent,
        DocumentUploadedEvent,
        # templates
        TemplateCreatedEvent,
        TemplatePublishedEvent,
        TemplateArchivedEvent,
    ]

    for event_type in event_types:

        async def _handler(event: object, _sf: object = session_factory) -> None:
            async with _sf() as session:  # type: ignore[operator]
                try:
                    repo = AuditLogRepositoryImpl(session=session)
                    service = AuditService(repository=repo)
                    subscriber = AuditEventSubscriber(service=service)
                    await subscriber.handle(event)  # type: ignore[arg-type]
                    await session.commit()
                except Exception:
                    await session.rollback()
                    import structlog

                    structlog.get_logger(__name__).exception(
                        "audit_event_subscription_failed",
                        event_type=type(event).__name__,
                    )

        event_bus.subscribe(event_type, _handler)


def _register_gateway_event_subscriptions() -> None:
    """注册 Gateway 工具同步事件订阅。

    在 init_db 之后调用，确保 session factory 已初始化。
    事件处理器使用独立的 DB session 以避免与发布侧 session 冲突。
    """
    from src.modules.tool_catalog.domain.events import ToolApprovedEvent, ToolDeprecatedEvent
    from src.modules.tool_catalog.infrastructure.external.gateway_event_handlers import (
        handle_tool_approved,
        handle_tool_deprecated,
    )
    from src.modules.tool_catalog.infrastructure.persistence.repositories.tool_repository_impl import (
        ToolRepositoryImpl,
    )
    from src.presentation.api.providers import get_gateway_sync
    from src.shared.domain.event_bus import event_bus
    from src.shared.infrastructure.database import get_session_factory

    session_factory = get_session_factory()
    gateway_sync = get_gateway_sync()

    async def _on_tool_approved(event: ToolApprovedEvent) -> None:
        async with session_factory() as session:
            try:
                repo = ToolRepositoryImpl(session=session)
                await handle_tool_approved(event, repo=repo, gateway_sync=gateway_sync)  # type: ignore[arg-type]
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def _on_tool_deprecated(event: ToolDeprecatedEvent) -> None:
        async with session_factory() as session:
            try:
                repo = ToolRepositoryImpl(session=session)
                await handle_tool_deprecated(event, repo=repo, gateway_sync=gateway_sync)  # type: ignore[arg-type]
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    event_bus.subscribe(ToolApprovedEvent, _on_tool_approved)
    event_bus.subscribe(ToolDeprecatedEvent, _on_tool_deprecated)


def _register_team_execution_event_subscriptions() -> None:
    """注册团队执行完成事件订阅 -> insights 成本归因。

    团队执行完成后，将 Token 消耗记录到 usage_records 表，
    实现跨模块成本追踪。
    """
    from src.modules.execution.domain.events import TeamExecutionCompletedEvent
    from src.modules.execution.infrastructure.persistence.repositories.team_execution_repository_impl import (
        TeamExecutionRepositoryImpl,
    )
    from src.modules.insights.application.dto.insights_dto import CreateUsageRecordDTO
    from src.modules.insights.application.services.insights_service import InsightsService
    from src.modules.insights.infrastructure.persistence.repositories.usage_record_repository_impl import (
        UsageRecordRepositoryImpl,
    )
    from src.shared.domain.event_bus import event_bus
    from src.shared.infrastructure.database import get_session_factory

    session_factory = get_session_factory()

    async def _on_team_execution_completed(event: TeamExecutionCompletedEvent) -> None:
        """团队执行完成后记录 Token 消耗到 insights 模块。"""
        if event.input_tokens == 0 and event.output_tokens == 0:
            return

        async with session_factory() as session:
            try:
                # 查询 TeamExecution 获取 agent_id 和 conversation_id
                exec_repo = TeamExecutionRepositoryImpl(session=session)
                execution = await exec_repo.get_by_id(event.execution_id)
                if execution is None:
                    return

                repo = UsageRecordRepositoryImpl(session=session)
                service = InsightsService(usage_repo=repo)

                dto = CreateUsageRecordDTO(
                    user_id=event.user_id,
                    agent_id=execution.agent_id,
                    conversation_id=execution.conversation_id,
                    model_id=event.model_id or "unknown",
                    tokens_input=event.input_tokens,
                    tokens_output=event.output_tokens,
                )
                await service.record_usage(dto)
                await session.commit()
            except Exception:
                await session.rollback()
                import structlog

                structlog.get_logger(__name__).exception(
                    "team_execution_cost_attribution_failed",
                    execution_id=event.execution_id,
                )

    event_bus.subscribe(TeamExecutionCompletedEvent, _on_team_execution_completed)


def _register_memory_extraction_event_subscriptions() -> None:
    """注册对话完成后记忆提取事件订阅。

    当 MEMORY_EXTRACTION_ENABLED=True 时，对话完成后自动从对话历史中
    提取长期记忆存储到 AgentCore Memory。
    """
    from src.modules.execution.domain.events import ConversationCompletedEvent
    from src.modules.execution.infrastructure.external.memory_adapter import MemoryAdapter
    from src.modules.execution.infrastructure.external.memory_extraction_handler import MemoryExtractionHandler
    from src.shared.domain.event_bus import event_bus
    from src.shared.infrastructure.database import get_session_factory

    settings = get_settings()
    if not settings.MEMORY_EXTRACTION_ENABLED:
        return

    session_factory = get_session_factory()
    memory_adapter = MemoryAdapter(
        memory_id=settings.AGENTCORE_MEMORY_ID,
        region=settings.AWS_REGION,
    )
    handler = MemoryExtractionHandler(
        memory_adapter=memory_adapter,
        session_factory=session_factory,
    )
    event_bus.subscribe(ConversationCompletedEvent, handler.handle_conversation_completed)


def _register_message_received_event_subscriptions() -> None:
    """注册普通对话消息接收事件订阅 -> insights 成本归因。

    助手回复消息后，将 Token 消耗记录到 usage_records 表，
    覆盖普通对话（非团队执行）的成本追踪。
    """
    from src.modules.execution.domain.events import MessageReceivedEvent
    from src.modules.execution.infrastructure.persistence.repositories.conversation_repository_impl import (
        ConversationRepositoryImpl,
    )
    from src.modules.insights.application.dto.insights_dto import CreateUsageRecordDTO
    from src.modules.insights.application.services.insights_service import InsightsService
    from src.modules.insights.infrastructure.persistence.repositories.usage_record_repository_impl import (
        UsageRecordRepositoryImpl,
    )
    from src.shared.domain.event_bus import event_bus
    from src.shared.infrastructure.database import get_session_factory

    session_factory = get_session_factory()

    async def _on_message_received(event: MessageReceivedEvent) -> None:
        """助手消息接收后记录 Token 消耗到 insights 模块。"""
        if event.token_count == 0:
            return

        async with session_factory() as session:
            try:
                # 通过 conversation_id 查询 Conversation 获取 agent_id 和 user_id
                conv_repo = ConversationRepositoryImpl(session=session)
                conversation = await conv_repo.get_by_id(event.conversation_id)
                if conversation is None:
                    return

                repo = UsageRecordRepositoryImpl(session=session)
                service = InsightsService(usage_repo=repo)

                # MessageReceivedEvent.token_count 未拆分 input/output,
                # 记为 tokens_input=token_count, tokens_output=0 (总量准确,
                # Cost Explorer 负责实际成本)
                dto = CreateUsageRecordDTO(
                    user_id=conversation.user_id,
                    agent_id=conversation.agent_id,
                    conversation_id=event.conversation_id,
                    model_id=event.model_id or "unknown",
                    tokens_input=event.token_count,
                    tokens_output=0,
                )
                await service.record_usage(dto)
                await session.commit()
            except Exception:
                await session.rollback()
                import structlog

                structlog.get_logger(__name__).exception(
                    "message_received_cost_attribution_failed",
                    conversation_id=event.conversation_id,
                    message_id=event.message_id,
                )

    event_bus.subscribe(MessageReceivedEvent, _on_message_received)


def register_all_event_subscriptions() -> None:
    """统一入口：注册所有事件订阅。"""
    _register_gateway_event_subscriptions()
    _register_team_execution_event_subscriptions()
    _register_message_received_event_subscriptions()
    _register_memory_extraction_event_subscriptions()
    _register_audit_event_subscriptions()
