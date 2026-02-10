"""FastAPI 应用入口。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.modules.agents.api.endpoints import router as agents_router
from src.modules.agents.domain.exceptions import AgentNameDuplicateError, AgentNotFoundError
from src.modules.auth.api.endpoints import router as auth_router
from src.modules.auth.domain.exceptions import AuthenticationError, AuthorizationError
from src.modules.execution.api.endpoints import router as execution_router
from src.modules.execution.domain.exceptions import (
    AgentNotAvailableError,
    ConversationNotActiveError,
    ConversationNotFoundError,
)
from src.modules.tool_catalog.api.endpoints import router as tool_catalog_router
from src.modules.tool_catalog.domain.exceptions import ToolNameDuplicateError, ToolNotFoundError
from src.presentation.api.routes.health import router as health_router
from src.shared.api.exception_handlers import register_exception_handlers, register_status_mapping
from src.shared.infrastructure.database import init_db
from src.shared.infrastructure.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期: 启动时初始化数据库连接。"""
    settings = get_settings()
    init_db(settings.database_url, echo=settings.APP_DEBUG)
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

    # CORS 中间件 — 禁止 allow_origins=["*"] + allow_credentials=True 组合
    # 生产环境应通过 CORS_ALLOWED_ORIGINS 环境变量配置具体域名
    cors_origins = settings.CORS_ALLOWED_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # 注册 auth 模块异常映射
    register_status_mapping(AuthenticationError, 401)
    register_status_mapping(AuthorizationError, 403)

    # 注册 agents 模块异常映射
    register_status_mapping(AgentNotFoundError, 404)
    register_status_mapping(AgentNameDuplicateError, 409)

    # 注册 execution 模块异常映射
    register_status_mapping(ConversationNotFoundError, 404)
    register_status_mapping(ConversationNotActiveError, 409)
    register_status_mapping(AgentNotAvailableError, 409)

    # 注册 tool_catalog 模块异常映射
    register_status_mapping(ToolNotFoundError, 404)
    register_status_mapping(ToolNameDuplicateError, 409)

    # 统一异常处理
    register_exception_handlers(app)

    # 路由
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(agents_router)
    app.include_router(execution_router)
    app.include_router(tool_catalog_router)

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
