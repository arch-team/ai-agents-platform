"""审计模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class AuditLogCreatedEvent(DomainEvent):
    """审计日志创建事件。"""

    audit_log_id: int = 0
    action: str = ""
    category: str = ""
    actor_id: int = 0
