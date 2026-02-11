"""Refresh Token API 端点集成测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_user_service
from src.modules.auth.application.dto.user_dto import TokenDTO
from src.modules.auth.domain.exceptions import (
    AuthenticationError,
    InvalidRefreshTokenError,
)
from src.presentation.api.main import create_app
from src.shared.api.middleware.rate_limit import limiter


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def app(mock_service):
    test_app = create_app()
    test_app.dependency_overrides[get_user_service] = lambda: mock_service
    limiter.reset()
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.mark.integration
class TestRefreshEndpoint:
    """POST /api/v1/auth/refresh tests."""

    def test_refresh_success(self, client, mock_service):
        """200 + 返回新的 TokenResponse。"""
        mock_service.refresh_access_token.return_value = TokenDTO(
            access_token="new-access-token",
            refresh_token="valid-refresh-token",
        )

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new-access-token"
        assert data["refresh_token"] == "valid-refresh-token"
        assert data["token_type"] == "bearer"

    def test_refresh_invalid_token(self, client, mock_service):
        """401 when refresh token is invalid."""
        mock_service.refresh_access_token.side_effect = InvalidRefreshTokenError()

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "INVALID_REFRESH_TOKEN"

    def test_refresh_inactive_user(self, client, mock_service):
        """401 when user is deactivated."""
        mock_service.refresh_access_token.side_effect = AuthenticationError("账户已停用")

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "AUTH_FAILED"

    def test_refresh_missing_body(self, client):
        """422 when request body is missing."""
        response = client.post("/api/v1/auth/refresh", json={})

        assert response.status_code == 422


@pytest.mark.integration
class TestLogoutEndpoint:
    """POST /api/v1/auth/logout tests."""

    def test_logout_success(self, client, mock_service):
        """200 + 返回成功消息。"""
        mock_service.logout.return_value = True

        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "some-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "已成功登出"
        mock_service.logout.assert_called_once_with("some-token")

    def test_logout_invalid_token(self, client, mock_service):
        """200 即使 token 不存在也返回成功（幂等设计）。"""
        mock_service.logout.return_value = False

        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "nonexistent-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "已成功登出"


@pytest.mark.integration
class TestLoginReturnsRefreshToken:
    """登录端点返回 refresh_token 的集成测试。"""

    def test_login_returns_refresh_token(self, client, mock_service):
        """200 + 返回 access_token 和 refresh_token。"""
        mock_service.login.return_value = TokenDTO(
            access_token="jwt-token",
            refresh_token="refresh-token-value",
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecurePassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "jwt-token"
        assert data["refresh_token"] == "refresh-token-value"
        assert data["token_type"] == "bearer"


@pytest.mark.integration
class TestRefreshTokenEndpointStructure:
    """新端点路由结构测试。"""

    def test_refresh_endpoint_exists(self, app):
        routes = [r.path for r in app.routes]
        assert "/api/v1/auth/refresh" in routes

    def test_logout_endpoint_exists(self, app):
        routes = [r.path for r in app.routes]
        assert "/api/v1/auth/logout" in routes
