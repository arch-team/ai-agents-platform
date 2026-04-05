"""集成测试: 三模式执行路由端到端验证。

验证 send_message 全流程中三模式路由的正确性:
- 模式1: runtime_arn → 主 runtime (AgentCoreRuntimeAdapter) + cwd="/workspace"
- 模式2: workspace_path → local runtime (ClaudeAgentAdapter) + 本地 cwd
- 模式3: V1 兼容 → 主 runtime + 内联 system_prompt
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.execution.application.dto.execution_dto import SendMessageDTO
from src.modules.execution.application.interfaces.agent_runtime import (
    AgentResponseChunk,
    IAgentRuntime,
)
from src.modules.execution.application.interfaces.llm_client import ILLMClient
from src.modules.execution.application.services.execution_service import ExecutionService
from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.entities.message import Message
from src.modules.execution.domain.repositories.conversation_repository import IConversationRepository
from src.modules.execution.domain.repositories.message_repository import IMessageRepository
from src.modules.execution.domain.value_objects.conversation_status import ConversationStatus
from src.modules.execution.domain.value_objects.message_role import MessageRole
from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo, IAgentQuerier


pytestmark = pytest.mark.integration


def _make_agent_info(
    *,
    runtime_arn: str = "",
    workspace_path: str = "",
    workspace_s3_uri: str = "",
) -> ActiveAgentInfo:
    return ActiveAgentInfo(
        id=1,
        name="测试 Agent",
        system_prompt="V1 系统提示词",
        model_id="anthropic.claude-3-5-sonnet",
        temperature=0.7,
        max_tokens=2048,
        top_p=1.0,
        runtime_type="agent",
        workspace_path=workspace_path,
        runtime_arn=runtime_arn,
        workspace_s3_uri=workspace_s3_uri,
    )


def _make_conversation() -> Conversation:
    return Conversation(id=1, title="测试对话", agent_id=1, user_id=100, status=ConversationStatus.ACTIVE)


def _make_message(msg_id: int = 1) -> Message:
    return Message(id=msg_id, conversation_id=1, role=MessageRole.USER, content="你好")


def _build_service(
    agent_info: ActiveAgentInfo,
    main_runtime: AsyncMock,
    local_runtime: AsyncMock | None = None,
) -> ExecutionService:
    """构建完整 mock 的 ExecutionService — 仅 runtime 路由逻辑走真实代码。"""
    conv_repo = AsyncMock(spec=IConversationRepository)
    conv_repo.get_by_id.return_value = _make_conversation()

    msg_repo = AsyncMock(spec=IMessageRepository)
    msg_repo.create.side_effect = lambda m: Message(
        id=10,
        conversation_id=m.conversation_id,
        role=m.role,
        content=m.content,
    )
    msg_repo.list_by_conversation.return_value = []

    agent_querier = AsyncMock(spec=IAgentQuerier)
    agent_querier.get_active_agent.return_value = agent_info

    return ExecutionService(
        conversation_repo=conv_repo,
        message_repo=msg_repo,
        llm_client=AsyncMock(spec=ILLMClient),
        agent_querier=agent_querier,
        agent_runtime=main_runtime,
        local_agent_runtime=local_runtime,
    )


@pytest.mark.asyncio
async def test_send_message_mode1_routes_to_main_runtime() -> None:
    """模式1 (runtime_arn): send_message 全流程路由到主 runtime。"""
    main_runtime = AsyncMock(spec=IAgentRuntime)
    main_runtime.execute.return_value = AgentResponseChunk(
        content="专属Runtime回复",
        done=True,
        input_tokens=10,
        output_tokens=20,
    )
    local_runtime = AsyncMock(spec=IAgentRuntime)

    agent_info = _make_agent_info(runtime_arn="arn:aws:bedrock:us-east-1:123:runtime/agent-1")
    service = _build_service(agent_info, main_runtime, local_runtime)

    with patch("src.modules.execution.application.services.execution_service.event_bus") as mock_bus:
        mock_bus.publish_async = AsyncMock()
        result = await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

    # 验证路由: 主 runtime 被调用, local 不被调用
    main_runtime.execute.assert_called_once()
    local_runtime.execute.assert_not_called()

    # 验证 AgentRequest 参数
    request = main_runtime.execute.call_args[0][0]
    assert request.runtime_arn == "arn:aws:bedrock:us-east-1:123:runtime/agent-1"
    assert request.cwd == "/workspace"
    assert request.system_prompt == ""
    assert result.content == "专属Runtime回复"


@pytest.mark.asyncio
async def test_send_message_mode2_routes_to_local_runtime() -> None:
    """模式2 (workspace_path): send_message 全流程路由到 local runtime。"""
    main_runtime = AsyncMock(spec=IAgentRuntime)
    local_runtime = AsyncMock(spec=IAgentRuntime)
    local_runtime.execute.return_value = AgentResponseChunk(
        content="本地预览回复",
        done=True,
        input_tokens=5,
        output_tokens=15,
    )

    agent_info = _make_agent_info(workspace_path="/data/agent-workspaces/42")
    service = _build_service(agent_info, main_runtime, local_runtime)

    with patch("src.modules.execution.application.services.execution_service.event_bus") as mock_bus:
        mock_bus.publish_async = AsyncMock()
        result = await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

    # 验证路由: local runtime 被调用, 主 runtime 不被调用
    local_runtime.execute.assert_called_once()
    main_runtime.execute.assert_not_called()

    # 验证 AgentRequest 参数
    request = local_runtime.execute.call_args[0][0]
    assert request.cwd == "/data/agent-workspaces/42"
    assert request.runtime_arn == ""
    assert request.system_prompt == ""
    assert result.content == "本地预览回复"


@pytest.mark.asyncio
async def test_send_message_mode3_v1_compatible() -> None:
    """模式3 (V1 兼容): send_message 全流程使用内联 system_prompt。"""
    main_runtime = AsyncMock(spec=IAgentRuntime)
    main_runtime.execute.return_value = AgentResponseChunk(
        content="V1回复",
        done=True,
        input_tokens=10,
        output_tokens=20,
    )

    agent_info = _make_agent_info()  # 无 runtime_arn, 无 workspace_path
    service = _build_service(agent_info, main_runtime)

    with patch("src.modules.execution.application.services.execution_service.event_bus") as mock_bus:
        mock_bus.publish_async = AsyncMock()
        result = await service.send_message(1, SendMessageDTO(content="你好"), user_id=100)

    main_runtime.execute.assert_called_once()

    # 验证 V1 兼容: system_prompt 保留, cwd/runtime_arn 为空
    request = main_runtime.execute.call_args[0][0]
    assert request.system_prompt == "V1 系统提示词"
    assert request.cwd == ""
    assert request.runtime_arn == ""
    assert result.content == "V1回复"
