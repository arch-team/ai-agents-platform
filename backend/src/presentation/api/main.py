"""FastAPI 应用入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.modules.agents.api.endpoints import router as agents_router
from src.modules.agents.domain.exceptions import AgentNameDuplicateError, AgentNotFoundError
from src.modules.audit.api.endpoints import router as audit_router
from src.modules.audit.domain.exceptions import AuditNotFoundError
from src.modules.auth.api.endpoints import router as auth_router
from src.modules.auth.domain.exceptions import (
    AccountLockedError,
    AuthenticationError,
    AuthorizationError,
    InvalidRefreshTokenError,
)
from src.modules.evaluation.api.endpoints import router as evaluation_router
from src.modules.evaluation.domain.exceptions import (
    EvaluationRunNotFoundError,
    TestCaseNotFoundError,
    TestSuiteEmptyError,
    TestSuiteNotActiveError,
    TestSuiteNotDeletableError,
    TestSuiteNotFoundError,
)
from src.modules.execution.api.endpoints import router as execution_router
from src.modules.execution.api.team_endpoints import router as team_execution_router
from src.modules.execution.domain.exceptions import (
    AgentNotAvailableError,
    ConversationNotActiveError,
    ConversationNotFoundError,
    TeamExecutionNotCancellableError,
    TeamExecutionNotFoundError,
)
from src.modules.insights.api.endpoints import router as insights_router
from src.modules.insights.domain.exceptions import (
    InvalidDateRangeError,
    UsageRecordNotFoundError,
)
from src.modules.knowledge.api.endpoints import router as knowledge_router
from src.modules.knowledge.domain.exceptions import (
    DocumentNotFoundError,
    KnowledgeBaseNameDuplicateError,
    KnowledgeBaseNotFoundError,
)
from src.modules.templates.api.endpoints import router as templates_router
from src.modules.templates.domain.exceptions import (
    DuplicateTemplateNameError,
    InvalidTemplateConfigError,
    TemplateNotFoundError,
)
from src.modules.tool_catalog.api.endpoints import router as tool_catalog_router
from src.modules.tool_catalog.domain.exceptions import ToolNameDuplicateError, ToolNotFoundError
from src.presentation.api.middleware.correlation import CorrelationIdMiddleware
from src.presentation.api.routes.health import router as health_router
from src.presentation.api.routes.stats import router as stats_router
from src.shared.api.exception_handlers import register_exception_handlers, register_status_mapping
from src.shared.api.middleware.rate_limit import setup_rate_limiting
from src.shared.domain.exceptions import TooManySSEConnectionsError
from src.shared.infrastructure.database import init_db
from src.shared.infrastructure.logging import setup_logging
from src.shared.infrastructure.settings import get_settings
from src.shared.infrastructure.tracing import setup_tracing


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.shared.domain.exceptions import DomainError


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
        AgentCreatedEvent, AgentUpdatedEvent, AgentActivatedEvent,
        AgentArchivedEvent, AgentDeletedEvent,
        # execution
        ConversationCreatedEvent, TeamExecutionStartedEvent,
        TeamExecutionCompletedEvent, TeamExecutionFailedEvent,
        # tool_catalog
        ToolCreatedEvent, ToolUpdatedEvent, ToolDeletedEvent,
        ToolSubmittedEvent, ToolApprovedAudit, ToolRejectedEvent, ToolDeprecatedAudit,
        # knowledge
        KnowledgeBaseCreatedEvent, KnowledgeBaseActivatedEvent,
        KnowledgeBaseDeletedEvent, DocumentUploadedEvent,
        # templates
        TemplateCreatedEvent, TemplatePublishedEvent, TemplateArchivedEvent,
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
    from src.modules.insights.infrastructure.external.bedrock_cost_calculator import BedrockCostCalculator
    from src.modules.insights.infrastructure.persistence.repositories.usage_record_repository_impl import (
        UsageRecordRepositoryImpl,
    )
    from src.shared.domain.event_bus import event_bus
    from src.shared.infrastructure.database import get_session_factory

    session_factory = get_session_factory()
    cost_calculator = BedrockCostCalculator()

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
                service = InsightsService(usage_repo=repo, cost_calculator=cost_calculator)

                dto = CreateUsageRecordDTO(
                    user_id=event.user_id,
                    agent_id=execution.agent_id,
                    conversation_id=execution.conversation_id,
                    model_id="anthropic.claude-sonnet",
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


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期: 启动时初始化数据库、日志、追踪和事件订阅。"""
    settings = get_settings()
    is_dev = settings.APP_ENV in ("development", "test")
    setup_logging(
        log_level=settings.LOG_LEVEL,
        is_dev=is_dev,
    )
    setup_tracing(
        service_name=settings.APP_NAME,
        is_dev=is_dev,
        otlp_endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        environment=settings.APP_ENV,
    )
    init_db(
        settings.database_url,
        echo=settings.APP_DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )
    _register_gateway_event_subscriptions()
    _register_team_execution_event_subscriptions()
    _register_audit_event_subscriptions()
    yield


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。"""
    settings = get_settings()
    app = FastAPI(
        title="AI Agents Platform",
        description="基于 Amazon Bedrock AgentCore 的企业级 AI Agents 平台",
        version="0.1.0",
        lifespan=lifespan,
        # 非开发环境禁用 docs, 避免暴露 API schema
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
    )

    # CORS 中间件 — 生产环境应通过 CORS_ALLOWED_ORIGINS 环境变量配置具体域名
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Correlation ID 中间件 — 为每个请求绑定唯一追踪 ID
    app.add_middleware(CorrelationIdMiddleware)

    # 注册各模块 DomainError 子类 → HTTP 状态码映射
    _module_exception_mappings: dict[type[DomainError], int] = {
        # auth
        AuthenticationError: 401,
        InvalidRefreshTokenError: 401,
        AccountLockedError: 423,
        AuthorizationError: 403,
        # agents
        AgentNotFoundError: 404,
        AgentNameDuplicateError: 409,
        # execution
        ConversationNotFoundError: 404,
        ConversationNotActiveError: 409,
        AgentNotAvailableError: 409,
        TeamExecutionNotFoundError: 404,
        TeamExecutionNotCancellableError: 409,
        # tool_catalog
        ToolNotFoundError: 404,
        ToolNameDuplicateError: 409,
        # knowledge
        KnowledgeBaseNotFoundError: 404,
        KnowledgeBaseNameDuplicateError: 409,
        DocumentNotFoundError: 404,
        # insights
        UsageRecordNotFoundError: 404,
        InvalidDateRangeError: 422,
        # templates
        TemplateNotFoundError: 404,
        DuplicateTemplateNameError: 409,
        InvalidTemplateConfigError: 422,
        # evaluation
        TestSuiteNotFoundError: 404,
        TestCaseNotFoundError: 404,
        EvaluationRunNotFoundError: 404,
        TestSuiteNotActiveError: 409,
        TestSuiteEmptyError: 409,
        TestSuiteNotDeletableError: 409,
        # audit
        AuditNotFoundError: 404,
        # shared — SSE 连接限制
        TooManySSEConnectionsError: 429,
    }
    for exc_type, status_code in _module_exception_mappings.items():
        register_status_mapping(exc_type, status_code)

    # 统一异常处理
    register_exception_handlers(app)

    # 路由
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(agents_router)
    app.include_router(execution_router)
    app.include_router(team_execution_router)
    app.include_router(tool_catalog_router)
    app.include_router(knowledge_router)
    app.include_router(insights_router)
    app.include_router(templates_router)
    app.include_router(evaluation_router)
    app.include_router(audit_router)
    app.include_router(stats_router)

    # Rate Limiting
    setup_rate_limiting(app)

    # OpenTelemetry FastAPI 自动追踪 (为所有 HTTP 请求生成 Span)
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)

    return app


app = create_app()


def run() -> None:
    """开发服务器入口。"""
    uvicorn.run(
        "src.presentation.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
