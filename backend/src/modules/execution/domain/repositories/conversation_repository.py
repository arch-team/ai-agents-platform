"""对话仓库接口。"""

from abc import abstractmethod

from src.modules.execution.domain.entities.conversation import Conversation
from src.shared.domain.repositories import IRepository


class IConversationRepository(IRepository[Conversation, int]):
    """对话仓库接口。"""

    @abstractmethod
    async def list_by_user(  # noqa: D102
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Conversation]: ...

    @abstractmethod
    async def count_by_user(  # noqa: D102
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
    ) -> int: ...
