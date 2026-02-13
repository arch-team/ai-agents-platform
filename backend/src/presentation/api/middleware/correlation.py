"""Correlation ID 中间件 — raw ASGI 实现。

为每个请求生成或接收 Correlation ID，注入到 structlog contextvars 和响应头中。
使用 raw ASGI 而非 BaseHTTPMiddleware，与 AuditMiddleware 保持一致，
避免 BaseHTTPMiddleware 的性能和 streaming 兼容性问题。
"""

from __future__ import annotations

import re
import uuid
from typing import TYPE_CHECKING

import structlog

from src.shared.infrastructure.tracing import inject_trace_context


if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send


CORRELATION_ID_HEADER = "X-Correlation-ID"

# 合法 Correlation ID 格式: UUID 或 1~128 位字母数字加连字符
_VALID_CORRELATION_ID_RE = re.compile(r"^[a-zA-Z0-9\-]{1,128}$")


def _sanitize_correlation_id(raw: str | None) -> str:
    """校验客户端提供的 Correlation ID，非法值使用自动生成值。"""
    if raw and _VALID_CORRELATION_ID_RE.match(raw):
        return raw
    return str(uuid.uuid4())


class CorrelationIdMiddleware:
    """为每个 HTTP 请求绑定 Correlation ID 和 Trace 上下文 (raw ASGI 实现)。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """从请求头提取或自动生成 correlation_id，注入 structlog 上下文和 trace 上下文。"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 从 scope headers 中提取 Correlation ID
        raw_correlation_id: str | None = None
        for header_name, header_value in scope.get("headers", []):
            if header_name.lower() == b"x-correlation-id":
                raw_correlation_id = header_value.decode("latin-1")
                break

        correlation_id = _sanitize_correlation_id(raw_correlation_id)

        # 提取 method 和 path
        method = scope.get("method", "")
        path = scope.get("path", "")

        # 注入 structlog contextvars, 后续所有 logger 调用自动携带
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=method,
            path=path,
        )

        # 注入 OpenTelemetry trace_id/span_id 到 structlog 上下文
        inject_trace_context()

        async def send_wrapper(message: object) -> None:
            if isinstance(message, dict) and message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-correlation-id", correlation_id.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)  # type: ignore[arg-type]

        await self.app(scope, receive, send_wrapper)
