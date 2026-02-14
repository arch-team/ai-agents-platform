"""MemoryExtractionHandler 单元测试。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.execution.domain.events import ConversationCompletedEvent
from src.modules.execution.infrastructure.external.memory_extraction_handler import MemoryExtractionHandler


def _make_event(*, conversation_id: int = 1, user_id: int = 10) -> ConversationCompletedEvent:
    return ConversationCompletedEvent(conversation_id=conversation_id, user_id=user_id)


def _make_message(*, role: str = "user", content: str = "hello") -> MagicMock:
    msg = MagicMock()
    msg.role = role
    msg.content = content
    return msg


def _make_conversation(*, agent_id: int = 42) -> MagicMock:
    conv = MagicMock()
    conv.agent_id = agent_id
    return conv


def _make_session_factory(session: MagicMock) -> MagicMock:
    """创建模拟 session_factory，支持 async with session_factory() as session。"""

    @asynccontextmanager
    async def _factory() -> AsyncIterator[MagicMock]:
        yield session

    return _factory


_HANDLER_MODULE = "src.modules.execution.infrastructure.external.memory_extraction_handler"


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryExtractionHandlerNormal:
    """handle_conversation_completed 正常提取记忆。"""

    @patch(f"{_HANDLER_MODULE}.MessageRepositoryImpl")
    @patch(f"{_HANDLER_MODULE}.ConversationRepositoryImpl")
    async def test_extracts_memories_from_conversation(
        self, mock_conv_repo_cls: MagicMock, mock_msg_repo_cls: MagicMock,
    ) -> None:
        # Arrange
        mock_session = MagicMock()
        mock_memory_adapter = AsyncMock()
        mock_memory_adapter.extract_memories.return_value = 2

        # 模拟 Conversation
        mock_conv_repo = AsyncMock()
        mock_conv_repo.get_by_id.return_value = _make_conversation(agent_id=42)
        mock_conv_repo_cls.return_value = mock_conv_repo

        # 模拟 Messages
        mock_msg_repo = AsyncMock()
        mock_msg_repo.list_by_conversation.return_value = [
            _make_message(role="user", content="hello"),
            _make_message(role="assistant", content="Hi there"),
        ]
        mock_msg_repo_cls.return_value = mock_msg_repo

        handler = MemoryExtractionHandler(
            memory_adapter=mock_memory_adapter,
            session_factory=_make_session_factory(mock_session),
        )

        # Act
        await handler.handle_conversation_completed(_make_event(conversation_id=1))

        # Assert
        mock_conv_repo.get_by_id.assert_called_once_with(1)
        mock_msg_repo.list_by_conversation.assert_called_once_with(1)
        mock_memory_adapter.extract_memories.assert_called_once_with(
            agent_id=42,
            conversation_content="user: hello\nassistant: Hi there",
            session_id="1",
        )


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryExtractionHandlerSkip:
    """跳过场景测试。"""

    @patch(f"{_HANDLER_MODULE}.MessageRepositoryImpl")
    @patch(f"{_HANDLER_MODULE}.ConversationRepositoryImpl")
    async def test_skips_when_conversation_not_found(
        self, mock_conv_repo_cls: MagicMock, mock_msg_repo_cls: MagicMock,  # noqa: ARG002
    ) -> None:
        mock_session = MagicMock()
        mock_memory_adapter = AsyncMock()

        mock_conv_repo = AsyncMock()
        mock_conv_repo.get_by_id.return_value = None
        mock_conv_repo_cls.return_value = mock_conv_repo

        handler = MemoryExtractionHandler(
            memory_adapter=mock_memory_adapter,
            session_factory=_make_session_factory(mock_session),
        )

        await handler.handle_conversation_completed(_make_event(conversation_id=999))

        mock_memory_adapter.extract_memories.assert_not_called()

    @patch(f"{_HANDLER_MODULE}.MessageRepositoryImpl")
    @patch(f"{_HANDLER_MODULE}.ConversationRepositoryImpl")
    async def test_skips_when_messages_empty(
        self, mock_conv_repo_cls: MagicMock, mock_msg_repo_cls: MagicMock,
    ) -> None:
        mock_session = MagicMock()
        mock_memory_adapter = AsyncMock()

        mock_conv_repo = AsyncMock()
        mock_conv_repo.get_by_id.return_value = _make_conversation(agent_id=42)
        mock_conv_repo_cls.return_value = mock_conv_repo

        mock_msg_repo = AsyncMock()
        mock_msg_repo.list_by_conversation.return_value = []
        mock_msg_repo_cls.return_value = mock_msg_repo

        handler = MemoryExtractionHandler(
            memory_adapter=mock_memory_adapter,
            session_factory=_make_session_factory(mock_session),
        )

        await handler.handle_conversation_completed(_make_event(conversation_id=1))

        mock_memory_adapter.extract_memories.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryExtractionHandlerError:
    """异常时记录日志但不中断。"""

    @patch(f"{_HANDLER_MODULE}.ConversationRepositoryImpl")
    async def test_exception_does_not_propagate(self, mock_conv_repo_cls: MagicMock) -> None:
        mock_session = MagicMock()
        mock_memory_adapter = AsyncMock()

        # 模拟 ConversationRepositoryImpl 查询时抛出异常
        mock_conv_repo = AsyncMock()
        mock_conv_repo.get_by_id.side_effect = Exception("db connection failed")
        mock_conv_repo_cls.return_value = mock_conv_repo

        handler = MemoryExtractionHandler(
            memory_adapter=mock_memory_adapter,
            session_factory=_make_session_factory(mock_session),
        )

        # 不应抛出异常
        await handler.handle_conversation_completed(_make_event(conversation_id=1))

        mock_memory_adapter.extract_memories.assert_not_called()
