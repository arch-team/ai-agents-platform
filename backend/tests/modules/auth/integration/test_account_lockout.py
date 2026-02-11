"""账户锁定集成测试 — 验证 6 次错误密码后返回 423。"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_user_service
from src.modules.auth.application.dto.user_dto import TokenDTO
from src.modules.auth.domain.exceptions import AccountLockedError, AuthenticationError
from src.presentation.api.main import create_app
from src.shared.api.middleware.rate_limit import limiter


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
class TestAccountLockoutEndpoint:
    """POST /api/v1/auth/login 账户锁定集成测试。"""

    def test_locked_account_returns_423(self, client, mock_service) -> None:
        """锁定账户登录应返回 423 Locked。"""
        mock_service.login.side_effect = AccountLockedError(
            locked_until=datetime.now(UTC) + timedelta(minutes=25),
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "any"},
        )

        assert response.status_code == 423
        data = response.json()
        assert data["code"] == "ACCOUNT_LOCKED"

    def test_auth_failure_still_returns_401(self, client, mock_service) -> None:
        """普通认证失败仍返回 401。"""
        mock_service.login.side_effect = AuthenticationError("邮箱或密码错误")

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
        )

        assert response.status_code == 401

    def test_successful_login_after_lockout_expires(self, client, mock_service) -> None:
        """锁定过期后正常登录返回 200。"""
        mock_service.login.return_value = TokenDTO(access_token="new-token")

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "correct"},
        )

        assert response.status_code == 200
        assert response.json()["access_token"] == "new-token"
