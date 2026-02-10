"""用户仓库实现。"""

from sqlalchemy import select

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.modules.auth.infrastructure.persistence.models.user_model import UserModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class UserRepositoryImpl(PydanticRepository[User, UserModel, int], IUserRepository):
    """用户仓库的 SQLAlchemy 实现。"""

    entity_class = User
    model_class = UserModel
    _updatable_fields: frozenset[str] = frozenset(
        {"name", "role", "is_active", "hashed_password", "updated_at"},
    )

    async def get_by_email(self, email: str) -> User | None:  # noqa: D102
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
