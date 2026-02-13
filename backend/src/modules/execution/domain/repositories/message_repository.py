"""消息仓库接口。"""

from abc import abstractmethod

from src.modules.execution.domain.entities.message import Message
from src.shared.domain.repositories import IRepository


class IMessageRepository(IRepository[Message, int]):
    """消息仓库接口。"""

    @abstractmethod
    async def list_by_conversation(  # noqa: D102
        self,
        conversation_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Message]: ...

    @abstractmethod
    async def count_by_conversation(self, conversation_id: int) -> int: ...  # noqa: D102
