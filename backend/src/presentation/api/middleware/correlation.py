"""Correlation ID 中间件。

为每个请求生成或接收 Correlation ID，注入到 structlog contextvars 和响应头中。
"""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.shared.infrastructure.tracing import inject_trace_context


CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """为每个 HTTP 请求绑定 Correlation ID 和 Trace 上下文。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """从请求头提取或自动生成 correlation_id，注入 structlog 上下文和 trace 上下文。"""
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())

        # 注入 structlog contextvars, 后续所有 logger 调用自动携带
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        # 注入 OpenTelemetry trace_id/span_id 到 structlog 上下文
        inject_trace_context()

        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
