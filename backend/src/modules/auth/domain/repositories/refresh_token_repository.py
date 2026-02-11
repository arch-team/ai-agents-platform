"""Refresh Token 仓库接口。"""

from abc import abstractmethod

from src.modules.auth.domain.entities.refresh_token import RefreshToken
from src.shared.domain.repositories import IRepository


class IRefreshTokenRepository(IRepository[RefreshToken, int]):
    """Refresh Token 仓库接口。"""

    @abstractmethod
    async def get_by_token(self, token: str) -> RefreshToken | None:
        """根据 Token 字符串查找。"""
        ...

    @abstractmethod
    async def revoke_by_user_id(self, user_id: int) -> int:
        """撤销指定用户的所有 Refresh Token，返回撤销数量。"""
        ...

    @abstractmethod
    async def revoke_by_token(self, token: str) -> bool:
        """撤销指定 Token，返回是否成功。"""
        ...

    @abstractmethod
    async def delete_expired(self) -> int:
        """删除所有已过期的 Token，返回删除数量。"""
        ...
