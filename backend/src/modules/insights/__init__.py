"""insights 模块 — 业务洞察与成本归因。"""

from src.modules.insights.api.endpoints import router
from src.modules.insights.application.services.insights_service import InsightsService
from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.modules.insights.domain.events import UsageRecordCreatedEvent


__all__ = [
    "InsightsService",
    "UsageRecord",
    "UsageRecordCreatedEvent",
    "router",
]
