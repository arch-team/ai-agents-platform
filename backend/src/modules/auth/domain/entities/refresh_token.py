"""Refresh Token 领域实体。"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pydantic import Field

from src.shared.domain.base_entity import PydanticEntity


def _generate_token() -> str:
    """生成随机 Token 字符串。"""
    return uuid4().hex


class RefreshToken(PydanticEntity):
    """Refresh Token 实体。"""

    token: str = Field(default_factory=_generate_token)
    user_id: int
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC) + timedelta(days=7),
    )
    revoked: bool = False

    @property
    def is_expired(self) -> bool:
        """检查 Token 是否已过期。"""
        return datetime.now(UTC) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """检查 Token 是否有效（未过期且未撤销）。"""
        return not self.revoked and not self.is_expired

    def revoke(self) -> None:
        """撤销 Token。"""
        self.revoked = True
        self.touch()
