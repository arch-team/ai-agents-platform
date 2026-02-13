"""审计模块领域异常。"""

from src.shared.domain.exceptions import DomainError, EntityNotFoundError


class AuditError(DomainError):
    """审计模块基础异常。"""

    def __init__(self, message: str = "审计错误") -> None:
        super().__init__(message=message, code="AUDIT_ERROR")


class AuditNotFoundError(EntityNotFoundError):
    """审计记录未找到。"""

    def __init__(self, audit_log_id: int) -> None:
        super().__init__(entity_type="AuditLog", entity_id=audit_log_id)
