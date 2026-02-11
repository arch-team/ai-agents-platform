"""Refresh Token 仓库实现。"""

from datetime import UTC, datetime

from sqlalchemy import delete, select, update

from src.modules.auth.domain.entities.refresh_token import RefreshToken
from src.modules.auth.domain.repositories.refresh_token_repository import (
    IRefreshTokenRepository,
)
from src.modules.auth.infrastructure.persistence.models.refresh_token_model import (
    RefreshTokenModel,
)
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class RefreshTokenRepositoryImpl(
    PydanticRepository[RefreshToken, RefreshTokenModel, int],
    IRefreshTokenRepository,
):
    """Refresh Token 仓库的 SQLAlchemy 实现。"""

    entity_class = RefreshToken
    model_class = RefreshTokenModel
    _updatable_fields: frozenset[str] = frozenset({"revoked", "updated_at"})

    async def get_by_token(self, token: str) -> RefreshToken | None:
        """根据 Token 字符串查找。"""
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token == token)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def revoke_by_user_id(self, user_id: int) -> int:
        """撤销指定用户的所有 Refresh Token。"""
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked.is_(False),
            )
            .values(revoked=True, updated_at=datetime.now(UTC))
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[attr-defined, no-any-return]

    async def revoke_by_token(self, token: str) -> bool:
        """撤销指定 Token。"""
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.token == token,
                RefreshTokenModel.revoked.is_(False),
            )
            .values(revoked=True, updated_at=datetime.now(UTC))
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return (result.rowcount or 0) > 0  # type: ignore[attr-defined]

    async def delete_expired(self) -> int:
        """删除所有已过期的 Token。"""
        now = datetime.now(UTC)
        stmt = delete(RefreshTokenModel).where(RefreshTokenModel.expires_at < now)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount or 0  # type: ignore[attr-defined]
