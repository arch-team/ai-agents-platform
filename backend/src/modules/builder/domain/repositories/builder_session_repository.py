"""BuilderSession 仓储接口。"""

from abc import abstractmethod

from src.modules.builder.domain.entities.builder_session import BuilderSession
from src.shared.domain.repositories import IRepository


class IBuilderSessionRepository(IRepository[BuilderSession, int]):
    """BuilderSession 仓储接口。"""

    @abstractmethod
    async def list_by_user(self, user_id: int, *, offset: int = 0, limit: int = 20) -> list[BuilderSession]:
        """查询指定用户的 Builder 会话列表。"""
        ...
