"""SSE 流式事件统一生成器 — 连接管理 + 错误处理。"""

import json
from collections.abc import AsyncIterator, Callable
from typing import Any

import structlog
from sse_starlette import ServerSentEvent

from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


async def stream_sse_events(
    sse_manager: Any,
    user_id: int,
    stream: AsyncIterator[Any],
    *,
    format_chunk: Callable[[Any], dict[str, object]],
    format_done: Callable[[], dict[str, object]] | None = None,
    log_event: str = "sse_stream_error",
    **log_context: object,
) -> AsyncIterator[ServerSentEvent]:
    """统一 SSE 流式事件生成器。

    封装 sse_manager 连接管理 + DomainError/通用异常处理,
    消除各端点中重复的 try/except + ServerSentEvent 样板代码。
    """
    async with sse_manager.connect(user_id):
        try:
            async for item in stream:
                yield ServerSentEvent(data=json.dumps(format_chunk(item)))
            if format_done is not None:
                yield ServerSentEvent(data=json.dumps(format_done()))
        except DomainError as e:
            yield ServerSentEvent(data=json.dumps({"error": e.message, "done": True}))
        except Exception:
            logger.exception(log_event, **log_context)
            yield ServerSentEvent(data=json.dumps({"error": "服务内部错误", "done": True}))
