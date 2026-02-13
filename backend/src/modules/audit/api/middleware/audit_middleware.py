"""审计中间件 — 自动记录 API 调用。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware

from src.modules.audit.application.dto.audit_log_dto import CreateAuditLogDTO
from src.modules.audit.application.services.audit_service import AuditService
from src.modules.audit.infrastructure.persistence.repositories.audit_log_repository_impl import (
    AuditLogRepositoryImpl,
)


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

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


class AuditMiddleware(BaseHTTPMiddleware):
    """审计中间件 — 异步记录 API 调用到审计日志。

    记录内容: method, path, status_code, actor_id, duration, ip_address, user_agent
    排除: 健康检查、文档等非业务端点
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """处理请求并异步记录审计日志。"""
        path = request.url.path

        # 排除非业务端点
        if _should_exclude(path):
            return await call_next(request)

        start_time = time.monotonic()
        response: Response = await call_next(request)
        duration_ms = (time.monotonic() - start_time) * 1000

        # 异步记录审计日志 — 不阻塞响应
        try:
            await self._record_audit(request, response, duration_ms)
        except Exception:
            logger.exception("audit_middleware_record_failed", path=path)

        return response

    async def _record_audit(
        self,
        request: Request,
        response: Response,
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
                    status_code=response.status_code,
                    result="success" if response.status_code < 400 else "failure",
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
