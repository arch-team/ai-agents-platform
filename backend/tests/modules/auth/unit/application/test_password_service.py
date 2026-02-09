"""密码哈希服务测试。"""

import pytest

from src.modules.auth.application.services.password_service import (
    hash_password,
    verify_password,
)


@pytest.mark.unit
class TestHashPassword:
    def test_hash_returns_string(self):
        result = hash_password("secret123")
        assert isinstance(result, str)

    def test_hash_differs_from_plaintext(self):
        result = hash_password("secret123")
        assert result != "secret123"

    def test_hash_starts_with_bcrypt_prefix(self):
        result = hash_password("secret123")
        assert result.startswith("$2b$")

    def test_different_calls_produce_different_hashes(self):
        h1 = hash_password("secret123")
        h2 = hash_password("secret123")
        assert h1 != h2


@pytest.mark.unit
class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        hashed = hash_password("correct-password")
        assert verify_password("correct-password", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False
