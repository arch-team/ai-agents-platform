"""工具绑定 E2E 集成测试。

验证 Agent 绑定工具 → 对话 → 工具传递到 Runtime 的全链路:
Agent.tool_ids → AgentQuerier → ToolQuerier.list_tools_for_agent()
→ ApprovedToolInfo[] → ExecutionService → IAgentRuntime
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.execution.application.dto.execution_dto import (
    SendMessageDTO,
    StreamChunk,
)
from src.modules.execution.application.interfaces.agent_runtime import (
    AgentRequest,
    AgentResponseChunk,
    AgentTool,
    IAgentRuntime,
)
from src.modules.execution.application.interfaces.gateway_auth import (
    IGatewayAuthService,
)
from src.modules.execution.application.interfaces.llm_client import (
    ILLMClient,
    LLMResponse,
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
from src.shared.domain.interfaces.tool_querier import (
    ApprovedToolInfo,
    IToolQuerier,
)


# ── 工厂函数 ──


def _make_agent_info(
    *,
    agent_id: int = 1,
    name: str = "测试 Agent",
    system_prompt: str = "你是一个助手",
    model_id: str = "anthropic.claude-3-5-sonnet",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    top_p: float = 1.0,
    runtime_type: str = "agent",
    tool_ids: tuple[int, ...] = (),
) -> ActiveAgentInfo:
    return ActiveAgentInfo(
        id=agent_id,
        name=name,
        system_prompt=system_prompt,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        runtime_type=runtime_type,
        tool_ids=tool_ids,
    )


def _make_approved_tool(
    *,
    tool_id: int = 1,
    name: str = "test-tool",
    description: str = "测试工具",
    tool_type: str = "mcp_server",
    server_url: str = "https://example.com/mcp",
    auth_type: str = "none",
) -> ApprovedToolInfo:
    return ApprovedToolInfo(
        id=tool_id,
        name=name,
        description=description,
        tool_type=tool_type,
        server_url=server_url,
        auth_type=auth_type,
    )


def _make_conversation(
    *,
    conv_id: int = 1,
    agent_id: int = 1,
    user_id: int = 100,
) -> Conversation:
    return Conversation(
        id=conv_id,
        title="测试对话",
        agent_id=agent_id,
        user_id=user_id,
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
    """创建基础 Mock: conv_repo, msg_repo, agent_querier, llm_client。"""
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


@pytest.mark.integration
class TestToolBindingQueryChain:
    """测试场景 1: 工具查询链路 — Agent.tool_ids → ToolQuerier → ApprovedToolInfo。"""

    @pytest.mark.asyncio
    async def test_agent_with_tools_passes_correct_tools_to_runtime(self) -> None:
        """Agent 绑定 tool_ids=[1,2] 时, ToolQuerier 返回对应已审批工具, Runtime 收到正确的 AgentTool 列表。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1, 2),
        )

        # 模拟 ToolQuerier 返回 2 个已审批工具
        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            _make_approved_tool(tool_id=1, name="search-tool", tool_type="mcp_server"),
            _make_approved_tool(tool_id=2, name="calc-api", tool_type="api", server_url="", auth_type="api_key"),
        ]

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="使用工具回复",
            done=True,
            input_tokens=10,
            output_tokens=20,
        )

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
            result = await service.send_message(1, SendMessageDTO(content="搜索一下"), user_id=100)

        assert result.content == "使用工具回复"

        # 验证 ToolQuerier 被正确调用
        tool_querier.list_tools_for_agent.assert_called_once_with(1)

        # 验证 Runtime 收到的 AgentRequest 包含正确工具
        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        assert len(request.tools) == 2
        assert request.tools[0].name == "search-tool"
        assert request.tools[0].tool_type == "mcp_server"
        assert request.tools[1].name == "calc-api"
        assert request.tools[1].tool_type == "api"

    @pytest.mark.asyncio
    async def test_tool_querier_called_with_agent_id(self) -> None:
        """验证 list_tools_for_agent 被调用时传入正确的 agent_id。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            agent_id=42,
            runtime_type="agent",
            tool_ids=(10,),
        )
        # conversation 的 agent_id 也需对齐
        conv_repo.get_by_id.return_value = _make_conversation(agent_id=42)

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            _make_approved_tool(tool_id=10, name="my-tool"),
        ]

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="ok",
            done=True,
            input_tokens=5,
            output_tokens=5,
        )

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
            await service.send_message(1, SendMessageDTO(content="hi"), user_id=100)

        # 验证 agent_id=42 被传递给 list_tools_for_agent
        tool_querier.list_tools_for_agent.assert_called_once_with(42)


@pytest.mark.integration
class TestToolPassingToRuntime:
    """测试场景 2: ExecutionService 工具传递 — 同步和流式路径。"""

    @pytest.mark.asyncio
    async def test_send_message_passes_tools_to_agent_runtime(self) -> None:
        """send_message (同步) 时 tools 参数正确传递给 IAgentRuntime.execute()。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1,),
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            _make_approved_tool(
                tool_id=1,
                name="weather-api",
                tool_type="api",
                server_url="",
            ),
        ]

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="天气: 晴",
            done=True,
            input_tokens=10,
            output_tokens=15,
        )

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
            await service.send_message(1, SendMessageDTO(content="天气如何"), user_id=100)

        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        assert len(request.tools) == 1
        tool: AgentTool = request.tools[0]
        assert tool.name == "weather-api"
        assert tool.tool_type == "api"

    @pytest.mark.asyncio
    async def test_stream_message_passes_tools_to_agent_runtime(self) -> None:
        """send_message_stream (流式) 时 tools 参数正确传递给 IAgentRuntime.execute_stream()。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        msg_repo.update.side_effect = lambda m: m
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1, 2),
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            _make_approved_tool(tool_id=1, name="mcp-search", tool_type="mcp_server"),
            _make_approved_tool(tool_id=2, name="func-tool", tool_type="function", server_url=""),
        ]

        async def _agent_gen() -> None:  # type: ignore[return]
            yield AgentResponseChunk(content="流式回复")
            yield AgentResponseChunk(done=True, input_tokens=5, output_tokens=10)

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute_stream.return_value = _agent_gen()

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
                SendMessageDTO(content="搜索"),
                user_id=100,
            )
            chunks: list[StreamChunk] = []
            async for chunk in stream:
                chunks.append(chunk)

        # 验证流正常完成
        assert any(c.content == "流式回复" for c in chunks)
        assert any(c.done for c in chunks)

        # 验证 Runtime 收到 2 个工具
        request: AgentRequest = agent_runtime.execute_stream.call_args.args[0]
        assert len(request.tools) == 2
        assert request.tools[0].name == "mcp-search"
        assert request.tools[1].name == "func-tool"


@pytest.mark.integration
class TestNoToolAgent:
    """测试场景 3: 无工具 Agent — tool_ids=[] 时 Runtime 收到空工具列表。"""

    @pytest.mark.asyncio
    async def test_agent_with_no_tools_sends_empty_tools(self) -> None:
        """tool_ids=() 时, ToolQuerier 返回空列表, Runtime 收到空工具列表。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(),
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = []

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="无工具回复",
            done=True,
            input_tokens=5,
            output_tokens=10,
        )

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

        assert result.content == "无工具回复"

        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        assert request.tools == []

    @pytest.mark.asyncio
    async def test_agent_without_tool_querier_sends_empty_tools(self) -> None:
        """未配置 tool_querier 时, Runtime 收到空工具列表。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1, 2),
        )

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="降级回复",
            done=True,
            input_tokens=5,
            output_tokens=10,
        )

        # 不传 tool_querier → 默认为 None
        service = ExecutionService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            agent_runtime=agent_runtime,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        assert result.content == "降级回复"
        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        assert request.tools == []


@pytest.mark.integration
class TestPartialToolInvalidation:
    """测试场景 4: 部分工具失效 — tool_ids 包含已废弃工具时, 只传递仍为 APPROVED 的工具。"""

    @pytest.mark.asyncio
    async def test_only_approved_tools_passed_to_runtime(self) -> None:
        """Agent 绑定 tool_ids=[1,2,3], 但工具 2 已废弃, Runtime 只收到工具 1 和 3。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1, 2, 3),
        )

        # ToolQuerier 只返回 APPROVED 的工具 (工具 2 已不返回)
        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            _make_approved_tool(tool_id=1, name="tool-a", tool_type="mcp_server"),
            _make_approved_tool(tool_id=3, name="tool-c", tool_type="function", server_url=""),
        ]

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="部分工具回复",
            done=True,
            input_tokens=10,
            output_tokens=15,
        )

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

        assert result.content == "部分工具回复"

        # 验证: Runtime 只收到 2 个工具 (跳过已废弃的工具 2)
        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        assert len(request.tools) == 2
        tool_names = [t.name for t in request.tools]
        assert "tool-a" in tool_names
        assert "tool-c" in tool_names

    @pytest.mark.asyncio
    async def test_all_tools_deprecated_sends_empty_list(self) -> None:
        """Agent 绑定的所有工具都已废弃时, Runtime 收到空工具列表。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1, 2),
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = []  # 全部废弃

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="无可用工具",
            done=True,
            input_tokens=5,
            output_tokens=10,
        )

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

        assert result.content == "无可用工具"
        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        assert request.tools == []


@pytest.mark.integration
class TestGatewayAuthIntegration:
    """测试场景 5: Gateway Auth 集成 — 有 mcp_server 工具时获取 Token。"""

    @pytest.mark.asyncio
    async def test_gateway_auth_called_when_mcp_tools_present(self) -> None:
        """存在 mcp_server 类型工具时, IGatewayAuthService.get_bearer_token() 被调用。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1,),
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            _make_approved_tool(tool_id=1, name="mcp-tool", tool_type="mcp_server"),
        ]

        gateway_auth = AsyncMock(spec=IGatewayAuthService)
        gateway_auth.get_bearer_token.return_value = "test-bearer-token"

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="认证回复",
            done=True,
            input_tokens=10,
            output_tokens=15,
        )

        service = ExecutionService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            agent_runtime=agent_runtime,
            tool_querier=tool_querier,
            gateway_auth=gateway_auth,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        # 验证 Gateway Auth 被调用
        gateway_auth.get_bearer_token.assert_called_once()

        # 验证 token 传递到 AgentRequest
        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        assert request.gateway_auth_token == "test-bearer-token"

    @pytest.mark.asyncio
    async def test_gateway_auth_not_called_without_mcp_tools(self) -> None:
        """只有 api/function 工具时, Gateway Auth 不被调用。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1,),
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            _make_approved_tool(tool_id=1, name="api-tool", tool_type="api", server_url=""),
        ]

        gateway_auth = AsyncMock(spec=IGatewayAuthService)
        gateway_auth.get_bearer_token.return_value = "should-not-be-called"

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="api 回复",
            done=True,
            input_tokens=10,
            output_tokens=15,
        )

        service = ExecutionService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            agent_runtime=agent_runtime,
            tool_querier=tool_querier,
            gateway_auth=gateway_auth,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        # 验证 Gateway Auth 未被调用
        gateway_auth.get_bearer_token.assert_not_called()

        # 验证 token 为空
        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        assert request.gateway_auth_token == ""

    @pytest.mark.asyncio
    async def test_gateway_auth_not_configured_returns_empty_token(self) -> None:
        """未配置 gateway_auth 时, token 为空字符串。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1,),
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            _make_approved_tool(tool_id=1, name="mcp-tool", tool_type="mcp_server"),
        ]

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="无认证回复",
            done=True,
            input_tokens=5,
            output_tokens=10,
        )

        # gateway_auth=None (未配置)
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
            await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        assert request.gateway_auth_token == ""

    @pytest.mark.asyncio
    async def test_gateway_auth_in_stream_mode(self) -> None:
        """流式模式: 有 mcp_server 工具时, Gateway Auth 被调用且 token 传递到 Runtime。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        msg_repo.update.side_effect = lambda m: m
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1,),
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            _make_approved_tool(tool_id=1, name="mcp-stream-tool", tool_type="mcp_server"),
        ]

        gateway_auth = AsyncMock(spec=IGatewayAuthService)
        gateway_auth.get_bearer_token.return_value = "stream-bearer-token"

        async def _agent_gen() -> None:  # type: ignore[return]
            yield AgentResponseChunk(content="流式认证回复")
            yield AgentResponseChunk(done=True, input_tokens=5, output_tokens=10)

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute_stream.return_value = _agent_gen()

        service = ExecutionService(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            llm_client=llm_client,
            agent_querier=agent_querier,
            agent_runtime=agent_runtime,
            tool_querier=tool_querier,
            gateway_auth=gateway_auth,
        )

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ) as mock_bus:
            mock_bus.publish_async = AsyncMock()
            stream = await service.send_message_stream(
                1,
                SendMessageDTO(content="搜索"),
                user_id=100,
            )
            chunks: list[StreamChunk] = []
            async for chunk in stream:
                chunks.append(chunk)

        # 验证流正常完成
        assert any(c.content == "流式认证回复" for c in chunks)

        # 验证 Gateway Auth 被调用
        gateway_auth.get_bearer_token.assert_called_once()

        # 验证 token 传递到 AgentRequest
        request: AgentRequest = agent_runtime.execute_stream.call_args.args[0]
        assert request.gateway_auth_token == "stream-bearer-token"


@pytest.mark.integration
class TestApprovedToolInfoToAgentToolConversion:
    """验证 ApprovedToolInfo → AgentTool 转换的字段映射。"""

    @pytest.mark.asyncio
    async def test_tool_config_fields_mapped_correctly(self) -> None:
        """ApprovedToolInfo 的配置字段正确映射到 AgentTool.config。"""
        conv_repo, msg_repo, agent_querier, llm_client = _setup_base_mocks()
        agent_querier.get_active_agent.return_value = _make_agent_info(
            runtime_type="agent",
            tool_ids=(1,),
        )

        tool_querier = AsyncMock(spec=IToolQuerier)
        tool_querier.list_tools_for_agent.return_value = [
            ApprovedToolInfo(
                id=1,
                name="custom-api",
                description="自定义 API 工具",
                tool_type="api",
                endpoint_url="https://api.example.com/v1/run",
                method="POST",
                auth_type="api_key",
            ),
        ]

        agent_runtime = AsyncMock(spec=IAgentRuntime)
        agent_runtime.execute.return_value = AgentResponseChunk(
            content="config 测试",
            done=True,
            input_tokens=5,
            output_tokens=10,
        )

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
            await service.send_message(1, SendMessageDTO(content="测试"), user_id=100)

        request: AgentRequest = agent_runtime.execute.call_args.args[0]
        tool: AgentTool = request.tools[0]

        # 验证字段映射
        assert tool.name == "custom-api"
        assert tool.description == "自定义 API 工具"
        assert tool.tool_type == "api"
        assert tool.config["endpoint_url"] == "https://api.example.com/v1/run"
        assert tool.config["method"] == "POST"
        assert tool.config["auth_type"] == "api_key"
