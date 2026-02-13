"""SSE 并发连接管理器。"""

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from src.shared.domain.exceptions import TooManySSEConnectionsError
from src.shared.infrastructure.settings import get_settings


class SSEConnectionManager:
    """管理每用户 SSE 并发连接数，防止资源耗尽。"""

    def __init__(self, max_connections_per_user: int = 5) -> None:
        self._max = max_connections_per_user
        self._connections: dict[int, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def connect(self, user_id: int) -> AsyncIterator[None]:
        """获取 SSE 连接槽位，超限时抛出 TooManySSEConnectionsError。"""
        async with self._lock:
            if self._connections[user_id] >= self._max:
                raise TooManySSEConnectionsError(
                    user_id=user_id, max_connections=self._max,
                )
            self._connections[user_id] += 1
        try:
            yield
        finally:
            async with self._lock:
                self._connections[user_id] -= 1
                if self._connections[user_id] <= 0:
                    del self._connections[user_id]

    @property
    def active_connections(self) -> dict[int, int]:
        """当前活跃连接数（用于监控）。"""
        return dict(self._connections)


@lru_cache
def get_sse_manager() -> SSEConnectionManager:
    """获取 SSEConnectionManager 单例。"""
    settings = get_settings()
    return SSEConnectionManager(
        max_connections_per_user=settings.SSE_MAX_CONNECTIONS_PER_USER,
    )
