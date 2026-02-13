"""Refresh Token 仓库接口。"""

from abc import abstractmethod

from src.modules.auth.domain.entities.refresh_token import RefreshToken
from src.shared.domain.repositories import IRepository


class IRefreshTokenRepository(IRepository[RefreshToken, int]):
    """Refresh Token 仓库接口。"""

    @abstractmethod
    async def get_by_token(self, token: str) -> RefreshToken | None: ...  # noqa: D102

    @abstractmethod
    async def revoke_by_user_id(self, user_id: int) -> int: ...  # noqa: D102

    @abstractmethod
    async def revoke_by_token(self, token: str) -> bool: ...  # noqa: D102

    @abstractmethod
    async def delete_expired(self) -> int: ...  # noqa: D102
