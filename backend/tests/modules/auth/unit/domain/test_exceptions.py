"""Auth 领域异常单元测试。"""

import pytest

from src.modules.auth.domain.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
)
from src.shared.domain.exceptions import AuthorizationError, DomainError, DuplicateEntityError


@pytest.mark.unit
class TestAuthenticationError:
    def test_default_message(self) -> None:
        error = AuthenticationError()
        assert error.message == "认证失败"
        assert error.code == "AUTH_FAILED"

    def test_custom_message(self) -> None:
        error = AuthenticationError("Token 已过期")
        assert error.message == "Token 已过期"

    def test_inherits_domain_error(self) -> None:
        assert issubclass(AuthenticationError, DomainError)


@pytest.mark.unit
class TestAuthorizationError:
    def test_default_message(self) -> None:
        error = AuthorizationError()
        assert error.message == "权限不足"
        assert error.code == "FORBIDDEN"

    def test_custom_message(self) -> None:
        error = AuthorizationError("需要管理员权限")
        assert error.message == "需要管理员权限"

    def test_inherits_domain_error(self) -> None:
        assert issubclass(AuthorizationError, DomainError)


@pytest.mark.unit
class TestUserAlreadyExistsError:
    def test_message_contains_email(self) -> None:
        error = UserAlreadyExistsError(email="test@example.com")
        assert "test@example.com" in error.message
        assert "User" in error.message

    def test_inherits_duplicate_entity_error(self) -> None:
        assert issubclass(UserAlreadyExistsError, DuplicateEntityError)

    def test_error_code(self) -> None:
        error = UserAlreadyExistsError(email="test@example.com")
        assert error.code == "DUPLICATE_USER"
