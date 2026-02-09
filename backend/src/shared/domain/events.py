"""领域事件基类。"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """领域事件基类，所有领域事件继承此类。自动生成唯一 ID 和时间戳。"""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None
