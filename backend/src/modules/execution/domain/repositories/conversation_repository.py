"""对话仓库接口。"""

from abc import abstractmethod

from src.modules.execution.domain.entities.conversation import Conversation
from src.shared.domain.repositories import IRepository


class IConversationRepository(IRepository[Conversation, int]):
    """对话仓库接口。"""

    @abstractmethod
    async def increment_message_stats(
        self, conversation_id: int, *, message_delta: int = 0, token_delta: int = 0,
    ) -> None:
        """原子增量更新消息计数和 Token 统计。

        使用 SQL `SET col = col + N` 避免行锁竞争 (不需要先 SELECT 再 UPDATE)。
        """

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
