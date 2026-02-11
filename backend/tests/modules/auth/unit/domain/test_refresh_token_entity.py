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
