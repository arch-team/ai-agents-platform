"""Auth API schemas 单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.auth.api.schemas.requests import LoginRequest, RegisterRequest
from src.modules.auth.api.schemas.responses import TokenResponse, UserResponse


@pytest.mark.unit
class TestRegisterRequest:
    def test_valid_request(self) -> None:
        req = RegisterRequest(email="test@example.com", password="Passw0rd!", name="Test")
        assert req.email == "test@example.com"
        assert req.name == "Test"

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError, match="email"):
            RegisterRequest(email="bad", password="Passw0rd!", name="Test")

    def test_short_password_raises(self) -> None:
        with pytest.raises(ValidationError, match="password"):
            RegisterRequest(email="test@example.com", password="short", name="Test")

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            RegisterRequest(email="test@example.com", password="Passw0rd!", name="")


@pytest.mark.unit
class TestLoginRequest:
    def test_valid_request(self) -> None:
        req = LoginRequest(email="test@example.com", password="Passw0rd!")
        assert req.email == "test@example.com"


@pytest.mark.unit
class TestUserResponse:
    def test_valid_response(self) -> None:
        resp = UserResponse(id=1, email="test@example.com", name="Test", role="viewer", is_active=True)
        assert resp.id == 1
        assert resp.role == "viewer"


@pytest.mark.unit
class TestTokenResponse:
    def test_default_token_type(self) -> None:
        resp = TokenResponse(access_token="abc.def.ghi")
        assert resp.token_type == "bearer"
