"""三模式执行路由测试。

测试 ExecutionService._build_agent_request() 的三模式路由逻辑:
- 模式1: runtime_arn → 专属 Runtime, cwd="/workspace", system_prompt 清空
- 模式2: workspace_path → 本地 cwd, system_prompt 清空
- 模式3: V1 兼容 → 内联 system_prompt (不变)

以及 _execute_agent / _create_agent_stream 的运行时选择:
- 模式1: 使用主 agent_runtime
- 模式2: 使用 local_agent_runtime (本地执行)
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.execution.application.interfaces.agent_runtime import (
    AgentRequest,
    AgentResponseChunk,
    IAgentRuntime,
)
from src.modules.execution.application.interfaces.llm_client import (
    ILLMClient,
    LLMMessage,
)
from src.modules.execution.application.services.execution_service import (
    ExecutionService,
    _SendContext,
)
from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.entities.message import Message
from src.modules.execution.domain.repositories.conversation_repository import (
    IConversationRepository,
)
from src.modules.execution.domain.repositories.message_repository import (
    IMessageRepository,
)
from src.modules.execution.domain.value_objects.message_role import MessageRole
from src.shared.domain.interfaces.agent_querier import (
    ActiveAgentInfo,
    IAgentQuerier,
)


def _make_agent_info(
    *,
    agent_id: int = 1,
    system_prompt: str = "你是一个助手",
    runtime_type: str = "agent",
    workspace_path: str = "",
    runtime_arn: str = "",
    workspace_s3_uri: str = "",
) -> ActiveAgentInfo:
    return ActiveAgentInfo(
        id=agent_id,
        name="测试 Agent",
        system_prompt=system_prompt,
        model_id="anthropic.claude-3-5-sonnet",
        temperature=0.7,
        max_tokens=2048,
        top_p=1.0,
        runtime_type=runtime_type,
        workspace_path=workspace_path,
        runtime_arn=runtime_arn,
        workspace_s3_uri=workspace_s3_uri,
    )


def _make_send_context(
    *,
    system_prompt: str = "你是一个助手",
    workspace_path: str = "",
    runtime_arn: str = "",
    workspace_s3_uri: str = "",
) -> _SendContext:
    """构造 _SendContext 测试数据。"""
    agent_info = _make_agent_info(
        system_prompt=system_prompt,
        workspace_path=workspace_path,
        runtime_arn=runtime_arn,
        workspace_s3_uri=workspace_s3_uri,
    )
    conversation = Conversation(id=1, title="测试", agent_id=1, user_id=100)
    user_msg = Message(id=1, conversation_id=1, role=MessageRole.USER, content="你好")
    return _SendContext(
        conversation=conversation,
        agent_info=agent_info,
        created_user_msg=user_msg,
        llm_messages=[LLMMessage(role="user", content="你好")],
        system_prompt=system_prompt,
    )


def _make_service(
    *,
    agent_runtime: AsyncMock | None = None,
    local_agent_runtime: AsyncMock | None = None,
) -> ExecutionService:
    return ExecutionService(
        conversation_repo=AsyncMock(spec=IConversationRepository),
        message_repo=AsyncMock(spec=IMessageRepository),
        llm_client=AsyncMock(spec=ILLMClient),
        agent_querier=AsyncMock(spec=IAgentQuerier),
        agent_runtime=agent_runtime,
        local_agent_runtime=local_agent_runtime,
    )


# ── _build_agent_request 三模式路由 ──


@pytest.mark.unit
class TestBuildAgentRequestRouting:
    """测试 _build_agent_request 根据 agent_info 字段路由到正确模式。"""

    def test_mode1_runtime_arn_sets_runtime_arn_and_workspace_cwd(self) -> None:
        """模式1: runtime_arn 存在 → AgentRequest.runtime_arn 设置, cwd="/workspace"。"""
        service = _make_service(agent_runtime=AsyncMock(spec=IAgentRuntime))
        ctx = _make_send_context(runtime_arn="arn:aws:bedrock:us-east-1:123:runtime/my-agent")

        request = service._build_agent_request(ctx, tools=[])

        assert request.runtime_arn == "arn:aws:bedrock:us-east-1:123:runtime/my-agent"
        assert request.cwd == "/workspace"

    def test_mode1_clears_system_prompt(self) -> None:
        """模式1: system_prompt 被清空 (CLAUDE.md 在 workspace 中提供)。"""
        service = _make_service(agent_runtime=AsyncMock(spec=IAgentRuntime))
        ctx = _make_send_context(
            system_prompt="原始提示词",
            runtime_arn="arn:aws:bedrock:us-east-1:123:runtime/my-agent",
        )

        request = service._build_agent_request(ctx, tools=[])

        assert request.system_prompt == ""

    def test_mode2_workspace_path_sets_cwd(self) -> None:
        """模式2: workspace_path 存在 → AgentRequest.cwd 设置为本地路径。"""
        service = _make_service(agent_runtime=AsyncMock(spec=IAgentRuntime))
        ctx = _make_send_context(workspace_path="/data/agent-workspaces/42")

        request = service._build_agent_request(ctx, tools=[])

        assert request.cwd == "/data/agent-workspaces/42"
        assert request.runtime_arn == ""

    def test_mode2_clears_system_prompt(self) -> None:
        """模式2: system_prompt 被清空 (CLAUDE.md 在 workspace 中提供)。"""
        service = _make_service(agent_runtime=AsyncMock(spec=IAgentRuntime))
        ctx = _make_send_context(
            system_prompt="原始提示词",
            workspace_path="/data/agent-workspaces/42",
        )

        request = service._build_agent_request(ctx, tools=[])

        assert request.system_prompt == ""

    def test_mode3_v1_keeps_system_prompt(self) -> None:
        """模式3: V1 兼容 → system_prompt 保留, cwd 和 runtime_arn 都为空。"""
        service = _make_service(agent_runtime=AsyncMock(spec=IAgentRuntime))
        ctx = _make_send_context(system_prompt="你是一个专业助手")

        request = service._build_agent_request(ctx, tools=[])

        assert request.system_prompt == "你是一个专业助手"
        assert request.cwd == ""
        assert request.runtime_arn == ""

    def test_mode1_takes_priority_over_mode2(self) -> None:
        """runtime_arn 和 workspace_path 同时存在时, 模式1 优先。"""
        service = _make_service(agent_runtime=AsyncMock(spec=IAgentRuntime))
        ctx = _make_send_context(
            runtime_arn="arn:aws:bedrock:us-east-1:123:runtime/my-agent",
            workspace_path="/data/agent-workspaces/42",
        )

        request = service._build_agent_request(ctx, tools=[])

        assert request.runtime_arn == "arn:aws:bedrock:us-east-1:123:runtime/my-agent"
        assert request.cwd == "/workspace"


# ── 运行时选择 ──


@pytest.mark.unit
class TestRuntimeSelection:
    """测试 _execute_agent 根据模式选择正确的 runtime adapter。"""

    @pytest.mark.asyncio
    async def test_mode2_uses_local_agent_runtime(self) -> None:
        """模式2 (workspace_path) 使用 local_agent_runtime 执行。"""
        main_runtime = AsyncMock(spec=IAgentRuntime)
        local_runtime = AsyncMock(spec=IAgentRuntime)
        local_runtime.execute.return_value = AgentResponseChunk(
            content="本地回复",
            done=True,
            input_tokens=10,
            output_tokens=20,
        )
        service = _make_service(
            agent_runtime=main_runtime,
            local_agent_runtime=local_runtime,
        )
        ctx = _make_send_context(workspace_path="/data/agent-workspaces/42")

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ):
            content, tokens = await service._execute_agent(ctx)

        # local_runtime 被调用, main_runtime 不被调用
        local_runtime.execute.assert_called_once()
        main_runtime.execute.assert_not_called()
        assert content == "本地回复"

    @pytest.mark.asyncio
    async def test_mode1_uses_main_agent_runtime(self) -> None:
        """模式1 (runtime_arn) 使用主 agent_runtime 执行。"""
        main_runtime = AsyncMock(spec=IAgentRuntime)
        main_runtime.execute.return_value = AgentResponseChunk(
            content="远程回复",
            done=True,
            input_tokens=10,
            output_tokens=20,
        )
        local_runtime = AsyncMock(spec=IAgentRuntime)
        service = _make_service(
            agent_runtime=main_runtime,
            local_agent_runtime=local_runtime,
        )
        ctx = _make_send_context(runtime_arn="arn:aws:bedrock:us-east-1:123:runtime/my-agent")

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ):
            content, tokens = await service._execute_agent(ctx)

        main_runtime.execute.assert_called_once()
        local_runtime.execute.assert_not_called()
        assert content == "远程回复"

    @pytest.mark.asyncio
    async def test_mode3_uses_main_agent_runtime(self) -> None:
        """模式3 (V1) 使用主 agent_runtime 执行。"""
        main_runtime = AsyncMock(spec=IAgentRuntime)
        main_runtime.execute.return_value = AgentResponseChunk(
            content="V1回复",
            done=True,
            input_tokens=10,
            output_tokens=20,
        )
        service = _make_service(agent_runtime=main_runtime)
        ctx = _make_send_context()

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ):
            content, tokens = await service._execute_agent(ctx)

        main_runtime.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_mode2_without_local_runtime_falls_back_to_main(self) -> None:
        """模式2 但 local_agent_runtime 未注入时, 降级使用主 runtime。"""
        main_runtime = AsyncMock(spec=IAgentRuntime)
        main_runtime.execute.return_value = AgentResponseChunk(
            content="降级回复",
            done=True,
            input_tokens=10,
            output_tokens=20,
        )
        service = _make_service(agent_runtime=main_runtime)
        ctx = _make_send_context(workspace_path="/data/agent-workspaces/42")

        with patch(
            "src.modules.execution.application.services.execution_service.event_bus",
        ):
            content, tokens = await service._execute_agent(ctx)

        main_runtime.execute.assert_called_once()


# ── AgentRequest.runtime_arn 字段 ──


@pytest.mark.unit
class TestAgentRequestRuntimeArn:
    """测试 AgentRequest 数据结构包含 runtime_arn 字段。"""

    def test_runtime_arn_default_empty(self) -> None:
        request = AgentRequest(prompt="test")
        assert request.runtime_arn == ""

    def test_runtime_arn_can_be_set(self) -> None:
        request = AgentRequest(
            prompt="test",
            runtime_arn="arn:aws:bedrock:us-east-1:123:runtime/my-agent",
        )
        assert request.runtime_arn == "arn:aws:bedrock:us-east-1:123:runtime/my-agent"
