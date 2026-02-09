"""Auth domain exceptions."""

from src.shared.domain.exceptions import DomainError, DuplicateEntityError


class AuthenticationError(DomainError):
    """认证失败。"""

    def __init__(self, message: str = "认证失败") -> None:
        super().__init__(message=message, code="AUTH_FAILED")


class AuthorizationError(DomainError):
    """授权失败。"""

    def __init__(self, message: str = "权限不足") -> None:
        super().__init__(message=message, code="FORBIDDEN")


class UserAlreadyExistsError(DuplicateEntityError):
    """用户已存在。"""

    def __init__(self, email: str) -> None:
        super().__init__(entity_type="User", field="email", value=email)
