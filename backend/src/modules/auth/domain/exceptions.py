"""认证模块领域异常。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.shared.domain.exceptions import DomainError, DuplicateEntityError


if TYPE_CHECKING:
    from datetime import datetime


class AuthenticationError(DomainError):
    """认证失败。"""

    def __init__(self, message: str = "认证失败") -> None:
        super().__init__(message=message, code="AUTH_FAILED")


class AccountLockedError(DomainError):
    """账户已锁定。"""

    def __init__(self, *, locked_until: datetime) -> None:
        self.locked_until = locked_until
        super().__init__(message="账户已锁定, 请稍后再试", code="ACCOUNT_LOCKED")


class AuthorizationError(DomainError):
    """授权失败。"""

    def __init__(self, message: str = "权限不足") -> None:
        super().__init__(message=message, code="FORBIDDEN")


class UserAlreadyExistsError(DuplicateEntityError):
    """用户已存在。"""

    def __init__(self, email: str) -> None:
        super().__init__(entity_type="User", field="email", value=email)
