"""用户仓库接口。"""

from abc import abstractmethod

from src.modules.auth.domain.entities.user import User
from src.shared.domain.repositories import IRepository


class IUserRepository(IRepository[User, int]):
    """用户仓库接口。"""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """根据邮箱查找用户。"""
        ...
