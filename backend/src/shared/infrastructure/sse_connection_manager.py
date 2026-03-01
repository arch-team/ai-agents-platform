"""SSE 并发连接管理器。"""

import asyncio
import contextlib
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from src.modules.execution.domain.exceptions import TooManySSEConnectionsError
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
                    user_id=user_id,
                    max_connections=self._max,
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
        """当前活跃连接数 (用于监控)。"""
        return dict(self._connections)

    @property
    def total_active_connections(self) -> int:
        """总活跃连接数。"""
        return sum(self._connections.values())

    @property
    def active_user_count(self) -> int:
        """当前有活跃 SSE 连接的用户数。"""
        return len(self._connections)

    async def publish_metrics(self) -> None:
        """推送 SSE 并发指标到 CloudWatch (asyncio.to_thread 包装 boto3)。"""
        total = self.total_active_connections
        user_count = self.active_user_count

        def _put_metrics() -> None:
            import boto3

            client = boto3.client("cloudwatch")
            client.put_metric_data(
                Namespace="SSEConnections",
                MetricData=[
                    {
                        "MetricName": "ActiveConnections",
                        "Value": float(total),
                        "Unit": "Count",
                    },
                    {
                        "MetricName": "ActiveUsers",
                        "Value": float(user_count),
                        "Unit": "Count",
                    },
                ],
            )

        with contextlib.suppress(Exception):
            await asyncio.to_thread(_put_metrics)


@lru_cache
def get_sse_manager() -> SSEConnectionManager:
    """获取 SSEConnectionManager 单例。"""
    settings = get_settings()
    return SSEConnectionManager(
        max_connections_per_user=settings.SSE_MAX_CONNECTIONS_PER_USER,
    )
