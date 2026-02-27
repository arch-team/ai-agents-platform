"""Querier 降级测试 — 验证 Querier 异常时 ExecutionService 不崩溃, 继续执行。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.execution.application.dto.execution_dto import (
    SendMessageDTO,
    StreamChunk,
)
from src.modules.execution.application.interfaces.agent_runtime import (
    AgentResponseChunk,
    IAgentRuntime,
)
from src.modules.execution.application.interfaces.llm_client import (
    ILLMClient,
    LLMResponse,
    LLMStreamChunk,
)
from src.modules.execution.application.interfaces.memory_service import (
    IMemoryService,
)
from src.modules.execution.application.services.execution_service import (
    ExecutionService,
)
from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.entities.message import Message
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
from src.shared.domain.interfaces.agent_querier import (
    ActiveAgentInfo,
    IAgentQuerier,
)
from src.shared.domain.interfaces.knowledge_querier import (
    IKnowledgeQuerier,
)
from src.shared.domain.interfaces.tool_querier import (
    IToolQuerier,
)


def _make_agent_info(
    *,
    runtime_type: str = "agent",
    knowledge_base_id: int | None = None,
    enable_memory: bool = False,
) -> ActiveAgentInfo:
    return ActiveAgentInfo(
        id=1,
        name="测试 Agent",
        system_prompt="你是一个助手",
        model_id="anthropic.claude-3-5-sonnet",
        temperature=0.7,
        max_tokens=2048,
        top_p=1.0,
        runtime_type=runtime_type,
        knowledge_base_id=knowledge_base_id,
        enable_memory=enable_memory,
    )


def _make_conversation() -> Conversation:
    return Conversation(
        id=1,
        title="测试对话",
        agent_id=1,
        user_id=100,
        status=ConversationStatus.ACTIVE,
    )


def _make_message(
    *,
    msg_id: int = 1,
    conversation_id: int = 1,
    role: MessageRole = MessageRole.USER,
    content: str = "你好",
) -> Message:
    return Message(
        id=msg_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        token_count=0,
    )


def _setup_base_mocks() -> tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
    """创建基础 Mock 对象。"""
    conv_repo = AsyncMock(spec=IConversationRepository)
    conv_repo.get_by_id.return_value = _make_conversation()
    conv_repo.update.side_effect = lambda c: c

    msg_repo = AsyncMock(spec=IMessageRepository)
    msg_repo.create.side_effect = lambda m: _make_message(
        conversation_id=m.conversation_id,
        role=m.role,
        content=m.content,
    )
    msg_repo.list_by_conversation.return_value = [_make_message(content="你好")]

    agent_querier = AsyncMock(spec=IAgentQuerier)

    llm_client = AsyncMock(spec=ILLMClient)
    llm_client.invoke.return_value = LLMResponse(
        content="正常回复",
        input_tokens=10,
        output_tokens=20,
    )

    return conv_repo, msg_repo, agent_querier, llm_client


@pytest.mark.unit
class TestToolQuerierDegradation:
    """IToolQuerier 异常时降级: 返回空工具列表, Agent 继续执行。"""

    @pytest.mark.asyncio
    async def test_tool_querier_exception_returns_empty_tools(self) -> None:
        """IToolQuerier.list_approved_tools 抛出异常时, Agent 以空工具继续执行。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(runtime_type="agent")

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="无工具降级回复",
            done=True,
            input_tokens=10,
            output_tokens=20,
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_approved_tools.side_effect = RuntimeError("连接超时")

        service = ExecutionService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            agent_runtime=agent_runtime,
            tool_querier=tool_querier,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        # 验证: 服务未崩溃, 正常返回
        assert result.content == "无工具降级回复"
        # 验证: agent_runtime 被调用, 且 request.tools 为空
        call_args = agent_runtime.execute.call_args
        request = call_args.args[0]
        assert request.tools == []

    @pytest.mark.asyncio
    async def test_tool_querier_exception_stream_continues(self) -> None:
        """流式模式: IToolQuerier 异常时, Agent 以空工具继续流式执行。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        msg_repo.update.side_effect = lambda m: m
        agent_querier.get_active_agent.return_value = _make_agent_info(runtime_type="agent")

        async def _agent_gen():  # type: ignore[no-untyped-def]
            yield AgentResponseChunk(content="降级流式")
            yield AgentResponseChunk(done=True, input_tokens=5, output_tokens=10)

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute_stream.return_value = _agent_gen()

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_approved_tools.side_effect = ConnectionError("网络不可达")

        service = ExecutionService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            agent_runtime=agent_runtime,
            tool_querier=tool_querier,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            stream = await service.send_message_stream(
                1,
                SendMessageDTO(content="你好"),
                user_id=100,
            )
            chunks: list[StreamChunk] = []
            async for chunk in stream:
                chunks.append(chunk)

        # 验证: 流正常完成
        assert any(c.done for c in chunks)
        assert any(c.content == "降级流式" for c in chunks)


@pytest.mark.unit
class TestKnowledgeQuerierDegradation:
    """IKnowledgeQuerier 异常时降级: 跳过 RAG 注入, 不阻塞对话。"""

    @pytest.mark.asyncio
    async def test_knowledge_querier_exception_skips_rag(self) -> None:
        """IKnowledgeQuerier.retrieve 抛出异常时, 跳过 RAG 注入, 正常回复。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="basic",
            knowledge_base_id=42,
        )

        knowledge_querier = AsyncMock(spec=IKnowledgeQuerier)
        knowledge_querier.retrieve.side_effect = RuntimeError("知识库服务不可用")

        service = ExecutionService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            knowledge_querier=knowledge_querier,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        # 验证: 服务未崩溃
        assert result.content == "正常回复"
        # 验证: LLM 调用的 system_prompt 不包含 RAG 上下文
        call_kwargs = llm_client.invoke.call_args.kwargs
        assert "知识库参考资料" not in call_kwargs["system_prompt"]

    @pytest.mark.asyncio
    async def test_knowledge_querier_exception_stream_skips_rag(self) -> None:
        """流式模式: IKnowledgeQuerier 异常时跳过 RAG, 正常流式回复。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        msg_repo.update.side_effect = lambda m: m
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="basic",
            knowledge_base_id=42,
        )

        async def _mock_stream(*_args: object, **_kwargs: object) -> object:
            async def _gen():  # type: ignore[no-untyped-def]
                yield LLMStreamChunk(content="流式回复")
                yield LLMStreamChunk(done=True, input_tokens=5, output_tokens=10)

            return _gen()

        llm_client.invoke_stream.side_effect = _mock_stream

        knowledge_querier = AsyncMock(spec=IKnowledgeQuerier)
        knowledge_querier.retrieve.side_effect = TimeoutError("检索超时")

        service = ExecutionService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            knowledge_querier=knowledge_querier,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            stream = await service.send_message_stream(
                1,
                SendMessageDTO(content="你好"),
                user_id=100,
            )
            chunks: list[StreamChunk] = []
            async for chunk in stream:
                chunks.append(chunk)

        # 验证: 流正常完成
        assert any(c.done for c in chunks)
        # 验证: system_prompt 不包含 RAG 上下文
        call_kwargs = llm_client.invoke_stream.call_args.kwargs
        assert "知识库参考资料" not in call_kwargs["system_prompt"]


@pytest.mark.unit
class TestMemoryServiceDegradation:
    """IMemoryService 异常时降级: 跳过记忆注入 (已有实现, 验证行为)。"""

    @pytest.mark.asyncio
    async def test_memory_service_exception_skips_injection(self) -> None:
        """IMemoryService.recall_memory 抛出异常时, 跳过记忆注入, 正常回复。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="basic",
            enable_memory=True,
        )

        memory_adapter = AsyncMock(spec=IMemoryService)
        memory_adapter.recall_memory.side_effect = RuntimeError("Memory 服务不可用")

        service = ExecutionService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            memory_adapter=memory_adapter,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        # 验证: 服务未崩溃
        assert result.content == "正常回复"
        # 验证: LLM 调用的 system_prompt 不包含记忆上下文
        call_kwargs = llm_client.invoke.call_args.kwargs
        assert "长期记忆" not in call_kwargs["system_prompt"]
