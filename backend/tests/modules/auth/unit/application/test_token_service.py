"""JWT Token 服务测试。"""

import pytest

from src.modules.auth.application.services.token_service import (
    create_access_token,
    decode_access_token,
)
from src.modules.auth.domain.exceptions import AuthenticationError

# 测试用 JWT 配置
_SECRET_KEY = "test-secret-key-for-jwt-minimum-32bytes!"
_ALGORITHM = "HS256"
_EXPIRE_MINUTES = 30


@pytest.mark.unit
class TestCreateAccessToken:
    def test_returns_string(self) -> None:
        token = create_access_token(
            "123", secret_key=_SECRET_KEY, algorithm=_ALGORITHM, expire_minutes=_EXPIRE_MINUTES,
        )
        assert isinstance(token, str)

    def test_token_has_three_parts(self) -> None:
        token = create_access_token(
            "123", secret_key=_SECRET_KEY, algorithm=_ALGORITHM, expire_minutes=_EXPIRE_MINUTES,
        )
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_contains_subject(self) -> None:
        token = create_access_token(
            "user-42", secret_key=_SECRET_KEY, algorithm=_ALGORITHM, expire_minutes=_EXPIRE_MINUTES,
        )
        payload = decode_access_token(token, secret_key=_SECRET_KEY, algorithm=_ALGORITHM)
        assert payload["sub"] == "user-42"

    def test_token_contains_extra_claims(self) -> None:
        token = create_access_token(
            "42",
            secret_key=_SECRET_KEY,
            algorithm=_ALGORITHM,
            expire_minutes=_EXPIRE_MINUTES,
            extra_claims={"role": "admin"},
        )
        payload = decode_access_token(token, secret_key=_SECRET_KEY, algorithm=_ALGORITHM)
        assert payload["role"] == "admin"

    def test_token_contains_exp_claim(self) -> None:
        token = create_access_token(
            "42", secret_key=_SECRET_KEY, algorithm=_ALGORITHM, expire_minutes=_EXPIRE_MINUTES,
        )
        payload = decode_access_token(token, secret_key=_SECRET_KEY, algorithm=_ALGORITHM)
        assert "exp" in payload


@pytest.mark.unit
class TestDecodeAccessToken:
    def test_decode_valid_token(self) -> None:
        token = create_access_token(
            "42", secret_key=_SECRET_KEY, algorithm=_ALGORITHM, expire_minutes=_EXPIRE_MINUTES,
        )
        payload = decode_access_token(token, secret_key=_SECRET_KEY, algorithm=_ALGORITHM)
        assert payload["sub"] == "42"

    def test_decode_invalid_token_raises(self) -> None:
        with pytest.raises(AuthenticationError, match="无效的认证令牌"):
            decode_access_token("invalid.token.here", secret_key=_SECRET_KEY, algorithm=_ALGORITHM)

    def test_decode_wrong_secret_raises(self) -> None:
        token = create_access_token(
            "42", secret_key=_SECRET_KEY, algorithm=_ALGORITHM, expire_minutes=_EXPIRE_MINUTES,
        )
        with pytest.raises(AuthenticationError):
            decode_access_token(token, secret_key="wrong-secret-key-minimum-32bytes-long!", algorithm=_ALGORITHM)
