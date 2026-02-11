"""insights 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class UsageRecordCreatedEvent(DomainEvent):
    """使用记录创建事件。"""

    record_id: int = 0
    user_id: int = 0
    agent_id: int = 0
    estimated_cost: float = 0.0
