"""EventBus 进程内事件总线测试。"""

from dataclasses import dataclass

import pytest
from cachetools import TTLCache

from src.shared.domain.event_bus import EventBus, event_bus, event_handler
from src.shared.domain.events import DomainEvent


@dataclass
class _TestEvent(DomainEvent):
    """用于测试的自定义事件。"""

    payload: str = ""


@pytest.mark.unit
class TestEventBus:
    """EventBus 进程内事件总线测试。"""

    def setup_method(self) -> None:
        """每个测试前创建新的 EventBus 实例。"""
        self.bus = EventBus()

    def test_subscribe_and_publish(self) -> None:
        """订阅后发布事件，处理器被调用。"""
        # Arrange
        received: list[_TestEvent] = []
        self.bus.subscribe(_TestEvent, received.append)
        event = _TestEvent(payload="hello")

        # Act
        self.bus.publish(event)

        # Assert
        assert len(received) == 1
        assert received[0].payload == "hello"

    def test_publish_to_multiple_subscribers(self) -> None:
        """同一事件类型多个订阅者都被调用。"""
        # Arrange
        received_a: list[_TestEvent] = []
        received_b: list[_TestEvent] = []
        self.bus.subscribe(_TestEvent, received_a.append)
        self.bus.subscribe(_TestEvent, received_b.append)
        event = _TestEvent(payload="multi")

        # Act
        self.bus.publish(event)

        # Assert
        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_publish_unsubscribed_event_no_error(self) -> None:
        """发布无订阅者的事件不报错。"""
        # Arrange
        event = _TestEvent(payload="nobody")

        # Act & Assert — 不应抛出异常
        self.bus.publish(event)

    def test_event_handler_decorator(self) -> None:
        """@event_handler 装饰器自动注册处理器到全局 event_bus。"""
        # Arrange — 先清除全局 event_bus 状态
        event_bus.clear()
        received: list[_TestEvent] = []

        @event_handler(_TestEvent)
        def on_test_event(event: _TestEvent) -> None:
            received.append(event)

        event = _TestEvent(payload="decorator")

        # Act
        event_bus.publish(event)

        # Assert
        assert len(received) == 1
        assert received[0].payload == "decorator"

        # Cleanup
        event_bus.clear()

    @pytest.mark.asyncio
    async def test_publish_async(self) -> None:
        """异步发布事件。"""
        # Arrange
        received: list[_TestEvent] = []
        self.bus.subscribe(_TestEvent, received.append)
        event = _TestEvent(payload="async")

        # Act
        await self.bus.publish_async(event)

        # Assert
        assert len(received) == 1
        assert received[0].payload == "async"

    def test_idempotent_handling(self) -> None:
        """幂等性：相同 event_id 的事件不重复处理。"""
        # Arrange
        received: list[_TestEvent] = []
        self.bus.subscribe(_TestEvent, received.append)
        event = _TestEvent(payload="once")

        # Act — 同一事件发布两次
        self.bus.publish(event)
        self.bus.publish(event)

        # Assert — 只处理一次
        assert len(received) == 1

    def test_clear_handlers(self) -> None:
        """清除所有已注册的处理器。"""
        # Arrange
        received: list[_TestEvent] = []
        self.bus.subscribe(_TestEvent, received.append)

        # Act
        self.bus.clear()
        self.bus.publish(_TestEvent(payload="after-clear"))

        # Assert — 清除后不再处理
        assert len(received) == 0

    def test_processed_event_ids_uses_ttl_cache(self) -> None:
        """_processed_event_ids 使用 TTLCache 实现，防止内存泄漏。"""
        assert isinstance(self.bus._processed_event_ids, TTLCache)

    def test_ttl_cache_expiry_allows_reprocessing(self) -> None:
        """TTLCache 过期后，相同 event_id 可被重新处理。"""
        # Arrange — 创建 TTL=0 的 EventBus 使缓存立即过期
        bus = EventBus()
        bus._processed_event_ids = TTLCache(maxsize=100, ttl=0)
        received: list[_TestEvent] = []
        bus.subscribe(_TestEvent, received.append)
        event = _TestEvent(payload="expire-test")

        # Act — 第一次发布
        bus.publish(event)
        # TTL=0 表示立即过期，再次发布应能处理
        bus.publish(event)

        # Assert — 两次都被处理（因为 TTL=0 缓存立即过期）
        assert len(received) == 2
