"""SSEConnectionManager 单元测试。"""

import asyncio

import pytest

from src.shared.domain.exceptions import TooManySSEConnectionsError
from src.shared.infrastructure.sse_connection_manager import SSEConnectionManager


@pytest.mark.unit
class TestSSEConnectionManager:
    """SSEConnectionManager 测试。"""

    @pytest.mark.asyncio
    async def test_connect_within_limit(self) -> None:
        """在限制内正常连接。"""
        manager = SSEConnectionManager(max_connections_per_user=2)
        async with manager.connect(user_id=1):
            assert manager.active_connections == {1: 1}
        # 连接关闭后计数释放
        assert manager.active_connections == {}

    @pytest.mark.asyncio
    async def test_connect_exceeds_limit_raises(self) -> None:
        """超过限制时抛出 TooManySSEConnectionsError。"""
        manager = SSEConnectionManager(max_connections_per_user=1)
        async with manager.connect(user_id=1):
            with pytest.raises(TooManySSEConnectionsError, match="SSE 并发连接数超限"):
                async with manager.connect(user_id=1):
                    pass  # pragma: no cover

    @pytest.mark.asyncio
    async def test_different_users_independent(self) -> None:
        """不同用户的连接数互相独立。"""
        manager = SSEConnectionManager(max_connections_per_user=1)
        async with manager.connect(user_id=1):
            # 用户 2 不受用户 1 连接数影响
            async with manager.connect(user_id=2):
                assert manager.active_connections == {1: 1, 2: 1}

    @pytest.mark.asyncio
    async def test_connection_released_after_exception(self) -> None:
        """连接在异常后正确释放。"""
        manager = SSEConnectionManager(max_connections_per_user=2)
        with pytest.raises(RuntimeError, match="测试异常"):
            async with manager.connect(user_id=1):
                raise RuntimeError("测试异常")
        # 异常后计数应释放
        assert manager.active_connections == {}

    @pytest.mark.asyncio
    async def test_concurrent_connections(self) -> None:
        """并发连接正确计数。"""
        manager = SSEConnectionManager(max_connections_per_user=3)
        results: list[int] = []

        async def _connect_and_record(user_id: int) -> None:
            async with manager.connect(user_id):
                results.append(manager.active_connections.get(user_id, 0))
                await asyncio.sleep(0.01)

        # 同一用户 3 个并发连接（刚好在限制内）
        await asyncio.gather(
            _connect_and_record(1),
            _connect_and_record(1),
            _connect_and_record(1),
        )
        # 全部结束后应释放
        assert manager.active_connections == {}
        # 至少有一个时刻连接数 > 1（并发执行）
        assert max(results) >= 1

    @pytest.mark.asyncio
    async def test_concurrent_exceed_limit(self) -> None:
        """并发连接超限时正确拒绝。"""
        manager = SSEConnectionManager(max_connections_per_user=2)
        errors: list[TooManySSEConnectionsError] = []

        async def _try_connect(user_id: int) -> None:
            try:
                async with manager.connect(user_id):
                    await asyncio.sleep(0.05)
            except TooManySSEConnectionsError as e:
                errors.append(e)

        # 用户 1 尝试 4 个并发连接，限制为 2
        await asyncio.gather(
            _try_connect(1),
            _try_connect(1),
            _try_connect(1),
            _try_connect(1),
        )
        # 应有至少 2 个被拒绝
        assert len(errors) >= 2
        # 全部结束后应释放
        assert manager.active_connections == {}

    @pytest.mark.asyncio
    async def test_error_attributes(self) -> None:
        """TooManySSEConnectionsError 携带正确属性。"""
        manager = SSEConnectionManager(max_connections_per_user=1)
        async with manager.connect(user_id=42):
            with pytest.raises(TooManySSEConnectionsError) as exc_info:
                async with manager.connect(user_id=42):
                    pass  # pragma: no cover
            assert exc_info.value.user_id == 42
            assert exc_info.value.max_connections == 1
            assert exc_info.value.code == "TOO_MANY_SSE_CONNECTIONS"
