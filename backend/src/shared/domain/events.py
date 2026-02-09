"""Domain event base class."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Domain event base class.

    All domain events inherit from this class.
    Each event automatically gets a unique ID and timestamp.
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None
