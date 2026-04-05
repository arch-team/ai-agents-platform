"""FastAPI 应用入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
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
    InvalidRefreshTokenError,
    SsoAuthError,
    SsoNotConfiguredError,
)
from src.modules.billing.api.endpoints import router as billing_router
from src.modules.billing.domain.exceptions import (
    BudgetExceededError,
    BudgetNotFoundError,
    DepartmentNotFoundError,
    DuplicateDepartmentCodeError,
)
from src.modules.builder.api.endpoints import router as builder_router
from src.modules.builder.domain.exceptions import BuilderSessionNotFoundError
from src.modules.evaluation.api.endpoints import router as evaluation_router
from src.modules.evaluation.domain.exceptions import (
    EvalPipelineNotFoundError,
    EvaluationRunNotFoundError,
    PipelineAlreadyRunningError,
    TestCaseNotFoundError,
    TestSuiteEmptyError,
    TestSuiteNotActiveError,
    TestSuiteNotDeletableError,
    TestSuiteNotFoundError,
)
from src.modules.execution.api.endpoints import router as execution_router
from src.modules.execution.api.preview_endpoints import router as preview_router
from src.modules.execution.api.team_endpoints import router as team_execution_router
from src.modules.execution.domain.exceptions import (
    AgentNotAvailableError,
    ConversationNotActiveError,
    ConversationNotFoundError,
    MemoryNotEnabledError,
    MessageNotFoundError,
    TeamExecutionNotCancellableError,
    TeamExecutionNotFoundError,
    TooManySSEConnectionsError,
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
from src.modules.skills.api.endpoints import router as skills_router
from src.modules.skills.domain.exceptions import SkillNotFoundError
from src.modules.templates.api.endpoints import router as templates_router
from src.modules.templates.domain.exceptions import (
    DuplicateTemplateNameError,
    InvalidTemplateConfigError,
    TemplateNotFoundError,
)
from src.modules.tool_catalog.api.endpoints import router as tool_catalog_router
from src.modules.tool_catalog.domain.exceptions import ToolNameDuplicateError, ToolNotFoundError
from src.presentation.api.event_subscriptions import register_all_event_subscriptions
from src.presentation.api.middleware.correlation import CorrelationIdMiddleware
from src.presentation.api.routes.health import router as health_router
from src.presentation.api.routes.stats import router as stats_router
from src.presentation.api.seed import recover_zombie_executions, seed_default_admin, seed_default_templates
from src.shared.api.exception_handlers import register_exception_handlers, register_status_mapping
from src.shared.api.middleware.rate_limit import setup_rate_limiting
from src.shared.domain.exceptions import AuthorizationError
from src.shared.infrastructure.database import init_db
from src.shared.infrastructure.logging import setup_logging
from src.shared.infrastructure.settings import get_settings
from src.shared.infrastructure.tracing import setup_tracing


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


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
    register_all_event_subscriptions()
    await seed_default_admin()
    logger.info("templates_seed_starting")
    await seed_default_templates()
    logger.info("templates_seed_done")
    await recover_zombie_executions()
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
        SsoAuthError: 401,
        SsoNotConfiguredError: 400,
        # agents
        AgentNotFoundError: 404,
        AgentNameDuplicateError: 409,
        # execution
        ConversationNotFoundError: 404,
        MessageNotFoundError: 404,
        ConversationNotActiveError: 409,
        AgentNotAvailableError: 409,
        MemoryNotEnabledError: 400,
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
        EvalPipelineNotFoundError: 404,
        PipelineAlreadyRunningError: 409,
        # audit
        AuditNotFoundError: 404,
        # builder
        BuilderSessionNotFoundError: 404,
        # skills
        SkillNotFoundError: 404,
        # billing
        DepartmentNotFoundError: 404,
        BudgetNotFoundError: 404,
        DuplicateDepartmentCodeError: 409,
        BudgetExceededError: 409,
        # shared — SSE 连接限制
        TooManySSEConnectionsError: 429,
    }
    for exc_type, status_code in _module_exception_mappings.items():
        register_status_mapping(exc_type, status_code)

    # 统一异常处理
    register_exception_handlers(app)

    # 路由
    from src.modules.auth.api.admin_endpoints import router as admin_router
    from src.modules.auth.api.sso_endpoints import router as sso_router
    from src.modules.execution.api.memory_endpoints import router as memory_router

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(sso_router)
    app.include_router(agents_router)
    app.include_router(billing_router)
    app.include_router(execution_router)
    app.include_router(team_execution_router)
    app.include_router(preview_router)
    app.include_router(memory_router)
    app.include_router(tool_catalog_router)
    app.include_router(knowledge_router)
    app.include_router(insights_router)
    app.include_router(templates_router)
    app.include_router(evaluation_router)
    app.include_router(audit_router)
    app.include_router(builder_router)
    app.include_router(skills_router)
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
