"""insights 领域层。"""

from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.modules.insights.domain.events import UsageRecordCreatedEvent
from src.modules.insights.domain.exceptions import (
    InsightsError,
    InvalidDateRangeError,
    UsageRecordNotFoundError,
)
from src.modules.insights.domain.repositories.usage_record_repository import (
    IUsageRecordRepository,
)


__all__ = [
    "IUsageRecordRepository",
    "InsightsError",
    "InvalidDateRangeError",
    "UsageRecord",
    "UsageRecordCreatedEvent",
    "UsageRecordNotFoundError",
]
