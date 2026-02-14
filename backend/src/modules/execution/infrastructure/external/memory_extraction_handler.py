"""对话完成后异步提取长期记忆。

订阅 ConversationCompletedEvent，从对话历史中提取有价值的记忆
存储到 AgentCore Memory，供后续对话上下文注入使用。
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.modules.execution.domain.events import ConversationCompletedEvent
from src.modules.execution.infrastructure.external.memory_adapter import MemoryAdapter
from src.modules.execution.infrastructure.persistence.repositories.conversation_repository_impl import (
    ConversationRepositoryImpl,
)
from src.modules.execution.infrastructure.persistence.repositories.message_repository_impl import (
    MessageRepositoryImpl,
)


logger = structlog.get_logger(__name__)


class MemoryExtractionHandler:
    """异步记忆提取处理器。"""

    def __init__(
        self, memory_adapter: MemoryAdapter, session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._memory_adapter = memory_adapter
        self._session_factory = session_factory

    async def handle_conversation_completed(self, event: ConversationCompletedEvent) -> None:
        """处理对话完成事件，提取并保存长期记忆。"""
        try:
            async with self._session_factory() as session:
                # 查询 Conversation 获取 agent_id
                conv_repo = ConversationRepositoryImpl(session=session)
                conversation = await conv_repo.get_by_id(event.conversation_id)
                if conversation is None:
                    logger.debug(
                        "memory_extraction_skip",
                        conversation_id=event.conversation_id,
                        reason="对话不存在",
                    )
                    return

                # 加载对话消息历史
                msg_repo = MessageRepositoryImpl(session=session)
                messages = await msg_repo.list_by_conversation(event.conversation_id)

                if not messages:
                    logger.debug(
                        "memory_extraction_skip",
                        conversation_id=event.conversation_id,
                        reason="对话消息为空",
                    )
                    return

                # 组装对话内容文本
                conversation_text = "\n".join(f"{msg.role}: {msg.content}" for msg in messages)

                count = await self._memory_adapter.extract_memories(
                    agent_id=conversation.agent_id,
                    conversation_content=conversation_text,
                    session_id=str(event.conversation_id),
                )
                logger.info(
                    "memory_extraction_completed",
                    conversation_id=event.conversation_id,
                    agent_id=conversation.agent_id,
                    extracted_count=count,
                )
        except Exception:
            logger.exception(
                "memory_extraction_handler_failed",
                conversation_id=event.conversation_id,
            )
