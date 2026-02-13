"""审计中间件 — 自动记录 API 调用（raw ASGI 实现）。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog
from starlette.requests import Request

from src.modules.audit.application.dto.audit_log_dto import CreateAuditLogDTO
from src.modules.audit.application.services.audit_service import AuditService
from src.modules.audit.infrastructure.persistence.repositories.audit_log_repository_impl import (
    AuditLogRepositoryImpl,
)


if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

logger = structlog.get_logger(__name__)

# 排除的非业务端点 — 不记录审计日志
_EXCLUDED_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    },
)

# 排除的路径前缀
_EXCLUDED_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
)


def _should_exclude(path: str) -> bool:
    """判断请求路径是否应排除审计记录。"""
    if path in _EXCLUDED_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _EXCLUDED_PREFIXES)


def _extract_actor_id(request: Request) -> int | None:
    """从请求的 state 中提取已认证用户 ID。"""
    return getattr(request.state, "audit_user_id", None)


class AuditMiddleware:
    """审计中间件 — raw ASGI 实现，避免 BaseHTTPMiddleware 的性能和 streaming 兼容性问题。

    记录内容: method, path, status_code, actor_id, duration, ip_address, user_agent
    排除: 健康检查、文档等非业务端点
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI 入口：仅拦截 HTTP 请求，其余直接透传。"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)
        path = request.url.path

        # 排除非业务端点
        if _should_exclude(path):
            await self.app(scope, receive, send)
            return

        start_time = time.monotonic()
        status_code = 500  # 默认值, send 回调中会更新

        async def send_wrapper(message: object) -> None:
            nonlocal status_code
            if isinstance(message, dict) and message.get("type") == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)  # type: ignore[arg-type]

        await self.app(scope, receive, send_wrapper)

        duration_ms = (time.monotonic() - start_time) * 1000

        # 异步记录审计日志 — 不阻塞响应
        try:
            await self._record_audit(request, status_code, duration_ms)
        except Exception:
            logger.exception("audit_middleware_record_failed", path=path)

    async def _record_audit(
        self,
        request: Request,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """记录 API 调用审计日志。"""
        from src.shared.infrastructure.database import get_session_factory

        actor_id = _extract_actor_id(request)
        # 未认证请求不记录审计日志 — 无法关联操作者
        if actor_id is None:
            return

        session_factory = get_session_factory()
        async with session_factory() as session:
            try:
                repo = AuditLogRepositoryImpl(session=session)
                service = AuditService(repository=repo)

                # 提取客户端信息
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")

                dto = CreateAuditLogDTO(
                    actor_id=actor_id,
                    actor_name=f"user:{actor_id}",
                    action="read" if request.method == "GET" else request.method.lower(),
                    category="system",
                    resource_type="api",
                    resource_id=request.url.path,
                    module="system",
                    ip_address=ip_address,
                    user_agent=user_agent[:500] if user_agent and len(user_agent) > 500 else user_agent,
                    request_method=request.method,
                    request_path=str(request.url.path),
                    status_code=status_code,
                    result="success" if status_code < 400 else "failure",
                    details={"duration_ms": round(duration_ms, 2)},
                )
                await service.record(dto)
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception(
                    "audit_middleware_db_failed",
                    path=request.url.path,
                )
