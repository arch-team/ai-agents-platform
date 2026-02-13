"""RefreshToken 实体测试。"""

from datetime import UTC, datetime, timedelta

import pytest

from src.modules.auth.domain.entities.refresh_token import RefreshToken


@pytest.mark.unit
class TestRefreshTokenEntity:
    def test_create_with_defaults(self) -> None:
        rt = RefreshToken(user_id=1)
        assert rt.user_id == 1
        assert rt.token != ""
        assert rt.revoked is False
        assert rt.expires_at > datetime.now(UTC)

    def test_token_is_unique(self) -> None:
        rt1 = RefreshToken(user_id=1)
        rt2 = RefreshToken(user_id=1)
        assert rt1.token != rt2.token

    def test_is_valid_when_fresh(self) -> None:
        rt = RefreshToken(user_id=1)
        assert rt.is_valid is True
        assert rt.is_expired is False

    def test_is_expired_when_past(self) -> None:
        rt = RefreshToken(
            user_id=1,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert rt.is_expired is True
        assert rt.is_valid is False

    def test_revoke_sets_revoked(self) -> None:
        rt = RefreshToken(user_id=1)
        assert rt.is_valid is True
        rt.revoke()
        assert rt.revoked is True
        assert rt.is_valid is False

    def test_revoked_token_is_invalid(self) -> None:
        rt = RefreshToken(user_id=1, revoked=True)
        assert rt.is_valid is False

    def test_custom_expires_at(self) -> None:
        future = datetime.now(UTC) + timedelta(days=14)
        rt = RefreshToken(user_id=1, expires_at=future)
        assert rt.expires_at == future
        assert rt.is_valid is True

    def test_token_has_sufficient_entropy(self) -> None:
        """Token 使用 secrets.token_urlsafe(32) 生成，长度 >= 43 字符（256 位）。"""
        rt = RefreshToken(user_id=1)
        # secrets.token_urlsafe(32) 生成 43 字符的 base64url 编码字符串
        assert len(rt.token) >= 43

    def test_token_is_url_safe(self) -> None:
        """Token 仅包含 URL 安全字符。"""
        import re

        rt = RefreshToken(user_id=1)
        # base64url: 字母、数字、连字符、下划线
        assert re.match(r"^[A-Za-z0-9_-]+$", rt.token)
