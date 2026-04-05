"""SSE 统一生成器测试。"""

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from src.shared.api.sse_helpers import stream_sse_events
from src.shared.domain.exceptions import DomainError


def _make_sse_manager() -> AsyncMock:
    """创建 SSE 连接管理器 Mock。"""
    manager = AsyncMock()

    @asynccontextmanager
    async def _connect(_user_id: int) -> AsyncIterator[None]:
        yield

    manager.connect = _connect
    return manager


async def _async_iter(*items: str) -> AsyncIterator[str]:
    for item in items:
        yield item


@pytest.mark.unit
class TestStreamSseEvents:
    """stream_sse_events 行为测试。"""

    @pytest.mark.asyncio
    async def test_yields_chunks_and_done(self) -> None:
        """正常流: chunk → chunk → done。"""
        events = []
        async for event in stream_sse_events(
            _make_sse_manager(),
            user_id=1,
            stream=_async_iter("hello", " world"),
            format_chunk=lambda c: {"content": c, "done": False},
            format_done=lambda: {"content": "", "done": True},
        ):
            events.append(json.loads(event.data))

        assert events == [
            {"content": "hello", "done": False},
            {"content": " world", "done": False},
            {"content": "", "done": True},
        ]

    @pytest.mark.asyncio
    async def test_no_done_event_when_format_done_is_none(self) -> None:
        """format_done=None 时不发送结束事件。"""
        events = []
        async for event in stream_sse_events(
            _make_sse_manager(),
            user_id=1,
            stream=_async_iter("data"),
            format_chunk=lambda c: {"c": c},
        ):
            events.append(json.loads(event.data))

        assert len(events) == 1
        assert events[0] == {"c": "data"}

    @pytest.mark.asyncio
    async def test_domain_error_yields_error_event(self) -> None:
        """DomainError 转为 SSE error 事件。"""

        async def _failing_stream() -> AsyncIterator[str]:
            raise DomainError(message="会话不存在")
            yield

        events = []
        async for event in stream_sse_events(
            _make_sse_manager(),
            user_id=1,
            stream=_failing_stream(),
            format_chunk=lambda c: {"content": c},
        ):
            events.append(json.loads(event.data))

        assert len(events) == 1
        assert events[0]["error"] == "会话不存在"
        assert events[0]["done"] is True

    @pytest.mark.asyncio
    async def test_generic_error_yields_internal_error(self) -> None:
        """通用异常转为"服务内部错误"事件。"""

        async def _crashing_stream() -> AsyncIterator[str]:
            raise RuntimeError("unexpected")
            yield

        events = []
        async for event in stream_sse_events(
            _make_sse_manager(),
            user_id=1,
            stream=_crashing_stream(),
            format_chunk=lambda c: {"content": c},
            log_event="test_error",
        ):
            events.append(json.loads(event.data))

        assert len(events) == 1
        assert events[0]["error"] == "服务内部错误"

    @pytest.mark.asyncio
    async def test_empty_stream_yields_only_done(self) -> None:
        """空流只发送 done 事件。"""

        async def _empty() -> AsyncIterator[str]:
            return
            yield

        events = []
        async for event in stream_sse_events(
            _make_sse_manager(),
            user_id=1,
            stream=_empty(),
            format_chunk=lambda c: {"content": c},
            format_done=lambda: {"done": True},
        ):
            events.append(json.loads(event.data))

        assert events == [{"done": True}]
