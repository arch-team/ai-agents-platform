"""用户仓库接口。"""

from abc import abstractmethod

from src.modules.auth.domain.entities.user import User
from src.shared.domain.repositories import IRepository


class IUserRepository(IRepository[User, int]):
    """用户仓库接口。"""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...  # noqa: D102

    @abstractmethod
    async def get_by_sso_subject(self, sso_provider: str, sso_subject: str) -> User | None:
        """根据 SSO 提供者和 Subject 查找用户。"""
        ...
