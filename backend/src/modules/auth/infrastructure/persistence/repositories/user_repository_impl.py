"""User repository implementation."""

from sqlalchemy import select

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.modules.auth.domain.value_objects.role import Role
from src.modules.auth.infrastructure.persistence.models.user_model import UserModel
from src.shared.infrastructure.pydantic_repository import PydanticRepository


class UserRepositoryImpl(PydanticRepository[User, UserModel, int], IUserRepository):
    """用户仓库的 SQLAlchemy 实现。"""

    entity_class = User
    model_class = UserModel
    _updatable_fields: frozenset[str] = frozenset({"name", "role", "is_active", "hashed_password", "updated_at"})

    def _to_entity(self, model: UserModel) -> User:
        """ORM Model -> User Entity 转换，显式处理 Role 枚举。"""
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            name=model.name,
            role=Role(model.role),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: User) -> UserModel:
        """User Entity -> ORM Model 转换，显式处理 Role 枚举。"""
        return UserModel(
            id=entity.id,
            email=entity.email,
            hashed_password=entity.hashed_password,
            name=entity.name,
            role=entity.role.value,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def get_by_email(self, email: str) -> User | None:
        """根据邮箱查找用户。"""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)
