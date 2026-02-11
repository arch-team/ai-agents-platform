"""注册端点权限保护 (REGISTRATION_ENABLED) 测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_user_service
from src.modules.auth.application.dto.user_dto import TokenDTO, UserDTO
from src.presentation.api.main import create_app
from src.shared.api.middleware.rate_limit import limiter
from src.shared.infrastructure.settings import Settings, get_settings


def _make_user_dto() -> UserDTO:
    return UserDTO(id=1, email="test@example.com", name="Test", role="viewer", is_active=True)


def _settings_enabled() -> Settings:
    """返回 REGISTRATION_ENABLED=True 的 Settings。"""
    return Settings(REGISTRATION_ENABLED=True)


def _settings_disabled() -> Settings:
    """返回 REGISTRATION_ENABLED=False 的 Settings。"""
    return Settings(REGISTRATION_ENABLED=False)


@pytest.mark.integration
class TestRegistrationEnabled:
    """REGISTRATION_ENABLED=True 时注册正常工作。"""

    def test_register_success_when_enabled(self):
        """注册开启时 201。"""
        mock_service = AsyncMock()
        mock_service.register.return_value = _make_user_dto()

        app = create_app()
        app.dependency_overrides[get_user_service] = lambda: mock_service
        app.dependency_overrides[get_settings] = _settings_enabled
        limiter.reset()
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePassword123", "name": "Test"},
        )

        assert response.status_code == 201


@pytest.mark.integration
class TestRegistrationDisabled:
    """REGISTRATION_ENABLED=False 时注册返回 403。"""

    def test_register_returns_403_when_disabled(self):
        """注册关闭时 403。"""
        mock_service = AsyncMock()

        app = create_app()
        app.dependency_overrides[get_user_service] = lambda: mock_service
        app.dependency_overrides[get_settings] = _settings_disabled
        limiter.reset()
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePassword123", "name": "Test"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "REGISTRATION_DISABLED"

    def test_register_disabled_does_not_call_service(self):
        """注册关闭时不调用 service.register。"""
        mock_service = AsyncMock()

        app = create_app()
        app.dependency_overrides[get_user_service] = lambda: mock_service
        app.dependency_overrides[get_settings] = _settings_disabled
        limiter.reset()
        client = TestClient(app)

        client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePassword123", "name": "Test"},
        )

        mock_service.register.assert_not_called()

    def test_login_works_when_registration_disabled(self):
        """注册关闭时登录仍然正常。"""
        mock_service = AsyncMock()
        mock_service.login.return_value = TokenDTO(access_token="jwt", refresh_token="rt")

        app = create_app()
        app.dependency_overrides[get_user_service] = lambda: mock_service
        app.dependency_overrides[get_settings] = _settings_disabled
        limiter.reset()
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "SecurePassword123"},
        )

        assert response.status_code == 200
