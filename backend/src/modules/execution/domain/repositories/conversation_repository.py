"""对话仓库接口。"""

from abc import abstractmethod

from src.modules.execution.domain.entities.conversation import Conversation
from src.shared.domain.repositories import IRepository


class IConversationRepository(IRepository[Conversation, int]):
    """对话仓库接口。"""

    @abstractmethod
    async def list_by_user(
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Conversation]:
        """按用户 ID 获取对话列表，可选按 Agent 过滤。"""

    @abstractmethod
    async def count_by_user(
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
    ) -> int:
        """按用户 ID 统计对话数量，可选按 Agent 过滤。"""
