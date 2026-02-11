"""Auth API endpoint integration tests."""

from unittest.mock import AsyncMock

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user, get_user_service, require_role
from src.modules.auth.application.dto.user_dto import TokenDTO, UserDTO
from src.modules.auth.domain.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
)
from src.modules.auth.domain.value_objects.role import Role
from src.presentation.api.main import create_app
from src.shared.api.middleware.rate_limit import limiter


def _make_user_dto(
    *,
    user_id: int = 1,
    email: str = "test@example.com",
    name: str = "Test User",
    role: str = "viewer",
    is_active: bool = True,
) -> UserDTO:
    return UserDTO(id=user_id, email=email, name=name, role=role, is_active=is_active)


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def app(mock_service):
    test_app = create_app()
    test_app.dependency_overrides[get_user_service] = lambda: mock_service
    # 重置 Rate Limiter 状态，避免测试间干扰
    limiter.reset()
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.mark.integration
class TestRegisterEndpoint:
    """POST /api/v1/auth/register tests."""

    def test_register_success(self, client, mock_service):
        """201 + returns UserResponse on success."""
        mock_service.register.return_value = _make_user_dto()

        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePassword123", "name": "Test User"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["role"] == "viewer"
        assert data["is_active"] is True
        mock_service.register.assert_called_once()

    def test_register_duplicate_email(self, client, mock_service):
        """409 when email already exists."""
        mock_service.register.side_effect = UserAlreadyExistsError("test@example.com")

        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePassword123", "name": "Test User"},
        )

        assert response.status_code == 409
        data = response.json()
        assert "DUPLICATE" in data["code"]

    def test_register_invalid_email(self, client):
        """422 for invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "SecurePassword123", "name": "Test User"},
        )

        assert response.status_code == 422

    def test_register_short_password(self, client):
        """422 for password shorter than 8 chars."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "short", "name": "Test User"},
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestLoginEndpoint:
    """POST /api/v1/auth/login tests."""

    def test_login_success(self, client, mock_service):
        """200 + returns TokenResponse on success."""
        mock_service.login.return_value = TokenDTO(access_token="jwt-token-here")

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecurePassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "jwt-token-here"
        assert data["token_type"] == "bearer"

    def test_login_wrong_credentials(self, client, mock_service):
        """401 for invalid credentials."""
        mock_service.login.side_effect = AuthenticationError("邮箱或密码错误")

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "AUTH_FAILED"

    def test_login_inactive_user(self, client, mock_service):
        """401 for inactive user."""
        mock_service.login.side_effect = AuthenticationError("账户已停用")

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "SecurePassword123"},
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestGetMeEndpoint:
    """GET /api/v1/auth/me tests."""

    def test_get_me_with_valid_token(self, app):
        """200 + returns UserResponse with valid token."""
        user_dto = _make_user_dto()
        app.dependency_overrides[get_current_user] = lambda: user_dto
        client = TestClient(app)

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    def test_get_me_without_token(self, client):
        """401 when no token provided."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_get_me_with_invalid_token(self, app):
        """401 when token is invalid."""

        async def _raise_auth_error():
            raise AuthenticationError("无效的认证令牌")

        app.dependency_overrides[get_current_user] = _raise_auth_error
        client = TestClient(app)

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestRBAC:
    """Role-based access control tests."""

    def test_require_role_authorized(self, app):
        """Admin user passes admin role check on protected endpoint."""
        # Arrange
        admin_user = _make_user_dto(role="admin")
        app.dependency_overrides[get_current_user] = lambda: admin_user

        admin_checker = require_role(Role.ADMIN)

        @app.get("/test-rbac-admin")
        async def _admin_endpoint(user: UserDTO = Depends(admin_checker)):
            return {"user": user.email}

        client = TestClient(app)

        # Act
        response = client.get(
            "/test-rbac-admin",
            headers={"Authorization": "Bearer valid-token"},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["user"] == "test@example.com"

    def test_require_role_forbidden(self, app):
        """Viewer user is forbidden from admin-only endpoint."""
        # Arrange
        viewer_user = _make_user_dto(role="viewer")
        app.dependency_overrides[get_current_user] = lambda: viewer_user

        admin_checker = require_role(Role.ADMIN)

        @app.get("/test-rbac-forbidden")
        async def _admin_endpoint(user: UserDTO = Depends(admin_checker)):
            return {"user": user.email}

        client = TestClient(app)

        # Act
        response = client.get(
            "/test-rbac-forbidden",
            headers={"Authorization": "Bearer valid-token"},
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "FORBIDDEN"


@pytest.mark.integration
class TestAuthEndpointsStructure:
    """Auth endpoint route structure tests."""

    def test_register_endpoint_exists(self, app):
        routes = [r.path for r in app.routes]
        assert "/api/v1/auth/register" in routes

    def test_login_endpoint_exists(self, app):
        routes = [r.path for r in app.routes]
        assert "/api/v1/auth/login" in routes

    def test_me_endpoint_exists(self, app):
        routes = [r.path for r in app.routes]
        assert "/api/v1/auth/me" in routes
