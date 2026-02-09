"""In-process event bus."""

from collections import defaultdict
from collections.abc import Callable

from src.shared.domain.events import DomainEvent


class EventBus:
    """In-process event bus.

    Supports synchronous and asynchronous event publishing and subscribing.
    Provides idempotency guarantee via _processed_event_ids.
    """

    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: dict[type[DomainEvent], list[Callable[..., object]]] = defaultdict(list)
        self._processed_event_ids: set[object] = set()

    def subscribe(self, event_type: type[DomainEvent], handler: Callable[..., object]) -> None:
        """Subscribe to an event type."""
        self._handlers[event_type].append(handler)

    async def publish_async(self, event: DomainEvent) -> None:
        """Publish event asynchronously (idempotent)."""
        if event.event_id in self._processed_event_ids:
            return
        self._processed_event_ids.add(event.event_id)
        for handler in self._handlers.get(type(event), []):
            result = handler(event)
            if hasattr(result, "__await__"):
                await result

    def publish(self, event: DomainEvent) -> None:
        """Publish event synchronously (idempotent)."""
        if event.event_id in self._processed_event_ids:
            return
        self._processed_event_ids.add(event.event_id)
        for handler in self._handlers.get(type(event), []):
            handler(event)

    def clear(self) -> None:
        """Clear all handlers and processed event records."""
        self._handlers.clear()
        self._processed_event_ids.clear()


# 全局事件总线实例
event_bus = EventBus()


def event_handler(event_type: type[DomainEvent]) -> Callable[..., object]:
    """Event handler decorator, auto-registers to global event_bus."""

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        event_bus.subscribe(event_type, func)
        return func

    return decorator
