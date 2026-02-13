"""审计事件订阅器接口。"""

from abc import ABC, abstractmethod

from src.shared.domain.events import DomainEvent


class IAuditEventSubscriber(ABC):
    """审计事件订阅器接口，用于订阅各模块 DomainEvent 并自动转换为 AuditLog 记录。"""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """处理领域事件，转换为审计日志记录。"""
