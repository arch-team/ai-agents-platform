"""FastAPI 应用入口。"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.modules.agents.api.endpoints import router as agents_router
from src.modules.agents.domain.exceptions import AgentNameDuplicateError, AgentNotFoundError
from src.modules.auth.api.endpoints import router as auth_router
from src.modules.auth.domain.exceptions import AuthenticationError, AuthorizationError
from src.presentation.api.routes.health import router as health_router
from src.shared.api.exception_handlers import register_exception_handlers, register_status_mapping


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。"""
    app = FastAPI(
        title="AI Agents Platform",
        description="基于 Amazon Bedrock AgentCore 的企业级 AI Agents 平台",
        version="0.1.0",
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 auth 模块异常映射
    register_status_mapping(AuthenticationError, 401)
    register_status_mapping(AuthorizationError, 403)

    # 注册 agents 模块异常映射
    register_status_mapping(AgentNotFoundError, 404)
    register_status_mapping(AgentNameDuplicateError, 409)

    # 统一异常处理
    register_exception_handlers(app)

    # 路由
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(agents_router)

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
