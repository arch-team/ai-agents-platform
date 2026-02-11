"""认证模块领域异常。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.shared.domain.exceptions import DomainError, DuplicateEntityError, ForbiddenError


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


class InvalidRefreshTokenError(DomainError):
    """Refresh Token 无效或已过期。"""

    def __init__(self, message: str = "Refresh Token 无效或已过期") -> None:
        super().__init__(message=message, code="INVALID_REFRESH_TOKEN")


class RegistrationDisabledError(ForbiddenError):
    """注册功能已禁用。"""

    def __init__(self) -> None:
        super().__init__(message="Public registration is disabled", code="REGISTRATION_DISABLED")


class UserAlreadyExistsError(DuplicateEntityError):
    """用户已存在。"""

    def __init__(self, email: str) -> None:
        super().__init__(entity_type="User", field="email", value=email)
