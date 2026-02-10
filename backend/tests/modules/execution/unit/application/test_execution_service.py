"""ExecutionService 测试。"""

import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.modules.execution.application.dto.execution_dto import (
    CreateConversationDTO,
    SendMessageDTO,
)
from src.modules.execution.application.interfaces.llm_client import (
    ILLMClient,
    LLMResponse,
    LLMStreamChunk,
)
from src.modules.execution.application.services.execution_service import (
    ExecutionService,
)
from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.entities.message import Message
from src.modules.execution.domain.exceptions import (
    AgentNotAvailableError,
    ConversationNotActiveError,
    ConversationNotFoundError,
)
from src.modules.execution.domain.repositories.conversation_repository import (
    IConversationRepository,
)
from src.modules.execution.domain.repositories.message_repository import (
    IMessageRepository,
)
from src.modules.execution.domain.value_objects.conversation_status import (
    ConversationStatus,
)
from src.modules.execution.domain.value_objects.message_role import MessageRole
from src.shared.domain.exceptions import DomainError
from src.shared.domain.interfaces.agent_querier import (
    ActiveAgentInfo,
    IAgentQuerier,
)
from src.shared.domain.interfaces.knowledge_querier import (
    IKnowledgeQuerier,
    RetrievalResult,
)


def _make_agent_info(
    *,
    agent_id: int = 1,
    name: str = "测试 Agent",
    system_prompt: str = "你是一个助手",
    model_id: str = "anthropic.claude-3-5-sonnet",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    top_p: float = 1.0,
    stop_sequences: tuple[str, ...] = (),
    knowledge_base_id: int | None = None,
) -> ActiveAgentInfo:
    return ActiveAgentInfo(
        id=agent_id,
        name=name,
        system_prompt=system_prompt,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stop_sequences=stop_sequences,
        knowledge_base_id=knowledge_base_id,
    )


def _make_conversation(
    *,
    conv_id: int = 1,
    title: str = "测试对话",
    agent_id: int = 1,
    user_id: int = 100,
    status: ConversationStatus = ConversationStatus.ACTIVE,
    message_count: int = 0,
    total_tokens: int = 0,
) -> Conversation:
    return Conversation(
        id=conv_id,
        title=title,
        agent_id=agent_id,
        user_id=user_id,
        status=status,
        message_count=message_count,
        total_tokens=total_tokens,
    )


def _make_message(
    *,
    msg_id: int = 1,
    conversation_id: int = 1,
    role: MessageRole = MessageRole.USER,
    content: str = "你好",
    token_count: int = 0,
) -> Message:
    return Message(
        id=msg_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        token_count=token_count,
    )


def _make_service(
    *,
    conv_repo: AsyncMock | None = None,
    msg_repo: AsyncMock | None = None,
    llm_client: AsyncMock | None = None,
    agent_querier: AsyncMock | None = None,
    stream_finalize_repos: tuple[AsyncMock, AsyncMock] | None = None,
    knowledge_querier: AsyncMock | None = None,
) -> ExecutionService:
    return ExecutionService(
        conversation_repo=conv_repo or AsyncMock(spec=IConversationRepository),
        message_repo=msg_repo or AsyncMock(spec=IMessageRepository),
        llm_client=llm_client or AsyncMock(spec=ILLMClient),
        agent_querier=agent_querier or AsyncMock(spec=IAgentQuerier),
        stream_finalize_repos=stream_finalize_repos,
        knowledge_querier=knowledge_querier,
    )


@pytest.mark.unit
class TestCreateConversation:
    @pytest.mark.asyncio
    async def test_create_conversation_success(self) -> None:
        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info()

        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.create.side_effect = lambda c: _make_conversation(
            title=c.title, agent_id=c.agent_id, user_id=c.user_id,
        )

        service = _make_service(conv_repo=conv_repo, agent_querier=agent_querier)
        dto = CreateConversationDTO(agent_id=1, title="我的对话")

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.create_conversation(dto, user_id=100)

        assert result.title == "我的对话"
        assert result.agent_id == 1
        assert result.user_id == 100
        assert result.status == "active"
        conv_repo.create.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_conversation_default_title(self) -> None:
        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info(name="小助手")

        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.create.side_effect = lambda c: _make_conversation(
            title=c.title, agent_id=c.agent_id, user_id=c.user_id,
        )

        service = _make_service(conv_repo=conv_repo, agent_querier=agent_querier)
        dto = CreateConversationDTO(agent_id=1)

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.create_conversation(dto, user_id=100)

        assert result.title == "与 小助手 的对话"

    @pytest.mark.asyncio
    async def test_create_conversation_agent_not_available(self) -> None:
        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = None

        service = _make_service(agent_querier=agent_querier)
        dto = CreateConversationDTO(agent_id=999)

        with pytest.raises(AgentNotAvailableError):
            await service.create_conversation(dto, user_id=100)


@pytest.mark.unit
class TestSendMessage:
    @pytest.mark.asyncio
    async def test_send_message_success(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation()
        conv_repo.update.side_effect = lambda c: c

        msg_repo = AsyncMock(spec=IMessageRepository)
        msg_repo.create.side_effect = lambda m: _make_message(
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            token_count=m.token_count,
        )
        msg_repo.list_by_conversation.return_value = [
            _make_message(content="你好"),
        ]

        llm_client = AsyncMock(spec=ILLMClient)
        llm_client.invoke.return_value = LLMResponse(
            content="你好！有什么可以帮助你？",
            input_tokens=10,
            output_tokens=20,
        )

        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info()

        service = _make_service(
            conv_repo=conv_repo,
            msg_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        assert result.role == "assistant"
        assert result.content == "你好！有什么可以帮助你？"
        assert result.token_count == 30
        assert msg_repo.create.call_count == 2  # 用户消息 + 助手消息
        llm_client.invoke.assert_called_once()
        conv_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_conversation_not_found(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = None

        service = _make_service(conv_repo=conv_repo)

        with pytest.raises(ConversationNotFoundError):
            await service.send_message(999, SendMessageDTO(content="你好"), user_id=100)

    @pytest.mark.asyncio
    async def test_send_message_not_active(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation(
            status=ConversationStatus.COMPLETED,
        )

        service = _make_service(conv_repo=conv_repo)

        with pytest.raises(ConversationNotActiveError):
            await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

    @pytest.mark.asyncio
    async def test_send_message_not_owner(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation(user_id=100)

        service = _make_service(conv_repo=conv_repo)

        with pytest.raises(DomainError, match="无权操作"):
            await service.send_message(1, SendMessageDTO(content="你好"), user_id=999)


@pytest.mark.unit
class TestSendMessageStream:
    @pytest.mark.asyncio
    async def test_send_message_stream_success(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation()
        conv_repo.update.side_effect = lambda c: c

        msg_repo = AsyncMock(spec=IMessageRepository)
        msg_repo.create.side_effect = lambda m: _make_message(
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            token_count=m.token_count,
        )
        msg_repo.list_by_conversation.return_value = [
            _make_message(content="你好"),
        ]
        msg_repo.update.side_effect = lambda m: m

        async def _mock_stream(*_args: object, **_kwargs: object) -> object:
            async def _gen():  # type: ignore[no-untyped-def]
                yield LLMStreamChunk(content="你好")
                yield LLMStreamChunk(content="！")
                yield LLMStreamChunk(done=True, input_tokens=10, output_tokens=20)
            return _gen()

        llm_client = AsyncMock(spec=ILLMClient)
        llm_client.invoke_stream.side_effect = _mock_stream

        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info()

        service = _make_service(
            conv_repo=conv_repo,
            msg_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            stream = await service.send_message_stream(
                1, SendMessageDTO(content="你好"), user_id=100,
            )

            events: list[str] = []
            async for event in stream:
                events.append(event)

        # 验证 SSE 事件
        assert len(events) == 3  # 2 content + 1 done
        first_data = json.loads(events[0].replace("data: ", "").strip())
        assert first_data["content"] == "你好"
        assert first_data["done"] is False

        last_data = json.loads(events[-1].replace("data: ", "").strip())
        assert last_data["done"] is True
        assert last_data["token_count"] == 30

        # 验证更新调用
        msg_repo.update.assert_called_once()
        conv_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_post_write_uses_independent_repos(self) -> None:
        """流后 DB 写操作应使用 stream_finalize_repos, 不依赖 DI repos。"""
        di_conv_repo = AsyncMock(spec=IConversationRepository)
        di_conv_repo.get_by_id.return_value = _make_conversation()

        di_msg_repo = AsyncMock(spec=IMessageRepository)
        di_msg_repo.create.side_effect = lambda m: _make_message(
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            token_count=m.token_count,
        )
        di_msg_repo.list_by_conversation.return_value = [_make_message(content="你好")]

        async def _mock_stream(*_args: object, **_kwargs: object) -> object:
            async def _gen():  # type: ignore[no-untyped-def]
                yield LLMStreamChunk(content="回复")
                yield LLMStreamChunk(done=True, input_tokens=5, output_tokens=10)
            return _gen()

        llm_client = AsyncMock(spec=ILLMClient)
        llm_client.invoke_stream.side_effect = _mock_stream

        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info()

        # 独立 session 的 repos (模拟 API 层通过独立 session 创建)
        stream_msg_repo = AsyncMock(spec=IMessageRepository)
        stream_msg_repo.update.side_effect = lambda m: m
        stream_conv_repo = AsyncMock(spec=IConversationRepository)
        stream_conv_repo.update.side_effect = lambda c: c

        service = _make_service(
            conv_repo=di_conv_repo,
            msg_repo=di_msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            stream_finalize_repos=(stream_msg_repo, stream_conv_repo),
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            stream = await service.send_message_stream(
                1, SendMessageDTO(content="你好"), user_id=100,
            )

            events: list[str] = []
            async for event in stream:
                events.append(event)

        # 验证: stream repos 执行了写操作
        stream_msg_repo.update.assert_called_once()
        stream_conv_repo.update.assert_called_once()
        # 验证: DI repos 的 update 未被调用
        di_msg_repo.update.assert_not_called()
        di_conv_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message_stream_conversation_not_found(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = None

        service = _make_service(conv_repo=conv_repo)

        with pytest.raises(ConversationNotFoundError):
            await service.send_message_stream(
                999, SendMessageDTO(content="你好"), user_id=100,
            )


@pytest.mark.unit
class TestGetConversation:
    @pytest.mark.asyncio
    async def test_get_conversation_success(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation()

        msg_repo = AsyncMock(spec=IMessageRepository)
        msg_repo.list_by_conversation.return_value = [
            _make_message(msg_id=1, role=MessageRole.USER, content="你好"),
            _make_message(msg_id=2, role=MessageRole.ASSISTANT, content="你好！"),
        ]

        service = _make_service(conv_repo=conv_repo, msg_repo=msg_repo)
        result = await service.get_conversation(1, user_id=100)

        assert result.conversation.id == 1
        assert result.conversation.title == "测试对话"
        assert len(result.messages) == 2
        assert result.messages[0].role == "user"
        assert result.messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = None

        service = _make_service(conv_repo=conv_repo)

        with pytest.raises(ConversationNotFoundError):
            await service.get_conversation(999, user_id=100)

    @pytest.mark.asyncio
    async def test_get_conversation_not_owner(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation(user_id=100)

        service = _make_service(conv_repo=conv_repo)

        with pytest.raises(DomainError, match="无权操作"):
            await service.get_conversation(1, user_id=999)


@pytest.mark.unit
class TestListConversations:
    @pytest.mark.asyncio
    async def test_list_conversations_with_data(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.list_by_user.return_value = [
            _make_conversation(conv_id=1, title="对话1"),
            _make_conversation(conv_id=2, title="对话2"),
        ]
        conv_repo.count_by_user.return_value = 2

        service = _make_service(conv_repo=conv_repo)
        result = await service.list_conversations(user_id=100)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.list_by_user.return_value = []
        conv_repo.count_by_user.return_value = 0

        service = _make_service(conv_repo=conv_repo)
        result = await service.list_conversations(user_id=100)

        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_conversations_by_agent_id(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.list_by_user.return_value = [
            _make_conversation(conv_id=1, agent_id=5),
        ]
        conv_repo.count_by_user.return_value = 1

        service = _make_service(conv_repo=conv_repo)
        result = await service.list_conversations(user_id=100, agent_id=5)

        assert result.total == 1
        conv_repo.list_by_user.assert_called_once_with(
            100, agent_id=5, offset=0, limit=20,
        )
        conv_repo.count_by_user.assert_called_once_with(
            100, agent_id=5,
        )


@pytest.mark.unit
class TestCompleteConversation:
    @pytest.mark.asyncio
    async def test_complete_conversation_success(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation()
        conv_repo.update.side_effect = lambda c: c

        service = _make_service(conv_repo=conv_repo)

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.complete_conversation(1, user_id=100)

        assert result.status == "completed"
        conv_repo.update.assert_called_once()
        mock_bus.publish_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_conversation_not_active(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation(
            status=ConversationStatus.COMPLETED,
        )

        service = _make_service(conv_repo=conv_repo)

        with pytest.raises(Exception):
            # complete() 在 Conversation 实体内部抛 InvalidStateTransitionError
            await service.complete_conversation(1, user_id=100)

    @pytest.mark.asyncio
    async def test_complete_conversation_not_owner(self) -> None:
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation(user_id=100)

        service = _make_service(conv_repo=conv_repo)

        with pytest.raises(DomainError, match="无权操作"):
            await service.complete_conversation(1, user_id=999)


@pytest.mark.unit
class TestRAGIntegration:
    """RAG 检索集成测试。"""

    @pytest.mark.asyncio
    async def test_send_message_with_rag_injects_context(self) -> None:
        """Agent 有 knowledge_base_id 时, LLM 收到的消息包含 RAG 上下文。"""
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation()
        conv_repo.update.side_effect = lambda c: c

        msg_repo = AsyncMock(spec=IMessageRepository)
        msg_repo.create.side_effect = lambda m: _make_message(
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            token_count=m.token_count,
        )
        msg_repo.list_by_conversation.return_value = [
            _make_message(content="你好"),
        ]

        llm_client = AsyncMock(spec=ILLMClient)
        llm_client.invoke.return_value = LLMResponse(
            content="回复内容",
            input_tokens=10,
            output_tokens=20,
        )

        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info(
            knowledge_base_id=42,
        )

        knowledge_querier = AsyncMock(spec=IKnowledgeQuerier)
        knowledge_querier.retrieve.return_value = [
            RetrievalResult(content="文档片段1", score=0.95),
            RetrievalResult(content="文档片段2", score=0.85),
        ]

        service = _make_service(
            conv_repo=conv_repo,
            msg_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            knowledge_querier=knowledge_querier,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        # 验证 knowledge_querier 被调用
        knowledge_querier.retrieve.assert_called_once_with(42, "你好", top_k=5)

        # 验证 LLM 收到的消息列表第一条是 RAG 上下文
        call_kwargs = llm_client.invoke.call_args
        messages = call_kwargs.kwargs["messages"]
        assert messages[0].role == "user"
        assert "参考资料" in messages[0].content
        assert "文档片段1" in messages[0].content
        assert "文档片段2" in messages[0].content

    @pytest.mark.asyncio
    async def test_send_message_without_kb_no_rag(self) -> None:
        """Agent 无 knowledge_base_id 时, 正常发送无 RAG。"""
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation()
        conv_repo.update.side_effect = lambda c: c

        msg_repo = AsyncMock(spec=IMessageRepository)
        msg_repo.create.side_effect = lambda m: _make_message(
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            token_count=m.token_count,
        )
        msg_repo.list_by_conversation.return_value = [
            _make_message(content="你好"),
        ]

        llm_client = AsyncMock(spec=ILLMClient)
        llm_client.invoke.return_value = LLMResponse(
            content="回复内容",
            input_tokens=10,
            output_tokens=20,
        )

        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info()

        knowledge_querier = AsyncMock(spec=IKnowledgeQuerier)

        service = _make_service(
            conv_repo=conv_repo,
            msg_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            knowledge_querier=knowledge_querier,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        # knowledge_querier 不应被调用
        knowledge_querier.retrieve.assert_not_called()

        # LLM 消息列表不应包含 RAG 上下文
        call_kwargs = llm_client.invoke.call_args
        messages = call_kwargs.kwargs["messages"]
        for msg in messages:
            assert "参考资料" not in msg.content

    @pytest.mark.asyncio
    async def test_send_message_stream_with_rag(self) -> None:
        """流式消息也注入 RAG 上下文。"""
        conv_repo = AsyncMock(spec=IConversationRepository)
        conv_repo.get_by_id.return_value = _make_conversation()
        conv_repo.update.side_effect = lambda c: c

        msg_repo = AsyncMock(spec=IMessageRepository)
        msg_repo.create.side_effect = lambda m: _make_message(
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            token_count=m.token_count,
        )
        msg_repo.list_by_conversation.return_value = [
            _make_message(content="你好"),
        ]
        msg_repo.update.side_effect = lambda m: m

        async def _mock_stream(*_args: object, **_kwargs: object) -> object:
            async def _gen():  # type: ignore[no-untyped-def]
                yield LLMStreamChunk(content="回复")
                yield LLMStreamChunk(done=True, input_tokens=5, output_tokens=10)
            return _gen()

        llm_client = AsyncMock(spec=ILLMClient)
        llm_client.invoke_stream.side_effect = _mock_stream

        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info(
            knowledge_base_id=42,
        )

        knowledge_querier = AsyncMock(spec=IKnowledgeQuerier)
        knowledge_querier.retrieve.return_value = [
            RetrievalResult(content="流式文档片段", score=0.9),
        ]

        service = _make_service(
            conv_repo=conv_repo,
            msg_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            knowledge_querier=knowledge_querier,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus"
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            stream = await service.send_message_stream(
                1, SendMessageDTO(content="你好"), user_id=100,
            )

            events: list[str] = []
            async for event in stream:
                events.append(event)

        # 验证 knowledge_querier 被调用
        knowledge_querier.retrieve.assert_called_once_with(42, "你好", top_k=5)

        # 验证 LLM 流式调用收到的消息包含 RAG 上下文
        call_kwargs = llm_client.invoke_stream.call_args
        messages = call_kwargs.kwargs["messages"]
        assert messages[0].role == "user"
        assert "参考资料" in messages[0].content
        assert "流式文档片段" in messages[0].content
