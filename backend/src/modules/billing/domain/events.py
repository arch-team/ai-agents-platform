"""Billing 领域事件。"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.shared.domain.events import DomainEvent


@dataclass
class DepartmentCreatedEvent(DomainEvent):
    """部门已创建事件。"""

    department_id: int = 0
    code: str = ""
    name: str = ""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None


@dataclass
class BudgetCreatedEvent(DomainEvent):
    """预算已创建事件。"""

    budget_id: int = 0
    department_id: int = 0
    year: int = 0
    month: int = 0
    budget_amount: float = 0.0
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None


@dataclass
class BudgetExceededEvent(DomainEvent):
    """预算已超支事件。"""

    budget_id: int = 0
    department_id: int = 0
    year: int = 0
    month: int = 0
    budget_amount: float = 0.0
    used_amount: float = 0.0
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None
