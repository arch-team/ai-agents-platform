"""进程内事件总线。"""

from collections import defaultdict
from collections.abc import Callable

from cachetools import TTLCache  # type: ignore[import-untyped]

from src.shared.domain.events import DomainEvent


# 已处理事件 ID 缓存配置: 最大 10 万条, 1 小时过期自动清理
_PROCESSED_EVENTS_MAXSIZE = 100_000
_PROCESSED_EVENTS_TTL = 3600


class EventBus:
    """进程内事件总线，支持同步/异步发布订阅，通过 event_id 保证幂等性。"""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Callable[..., object]]] = defaultdict(list)
        self._processed_event_ids: TTLCache[object, bool] = TTLCache(
            maxsize=_PROCESSED_EVENTS_MAXSIZE,
            ttl=_PROCESSED_EVENTS_TTL,
        )

    def subscribe(self, event_type: type[DomainEvent], handler: Callable[..., object]) -> None:
        """订阅事件类型。"""
        self._handlers[event_type].append(handler)

    def _mark_processed(self, event: DomainEvent) -> bool:
        """标记事件为已处理，返回是否为首次处理。"""
        if event.event_id in self._processed_event_ids:
            return False
        self._processed_event_ids[event.event_id] = True
        return True

    async def publish_async(self, event: DomainEvent) -> None:
        """异步发布事件（幂等）。"""
        if not self._mark_processed(event):
            return
        for handler in self._handlers.get(type(event), []):
            result = handler(event)
            if hasattr(result, "__await__"):
                await result

    def publish(self, event: DomainEvent) -> None:
        """同步发布事件（幂等）。"""
        if not self._mark_processed(event):
            return
        for handler in self._handlers.get(type(event), []):
            handler(event)

    def clear(self) -> None:
        """清空所有处理器和已处理事件记录。"""
        self._handlers.clear()
        self._processed_event_ids.clear()


# 全局事件总线实例
event_bus = EventBus()


def event_handler(event_type: type[DomainEvent]) -> Callable[..., object]:
    """事件处理器装饰器，自动注册到全局 event_bus。"""

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        event_bus.subscribe(event_type, func)
        return func

    return decorator
