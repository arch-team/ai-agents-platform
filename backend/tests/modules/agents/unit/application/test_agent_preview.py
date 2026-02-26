"""Agent 预览端点单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.api.preview_endpoints import PreviewAgentRequest, preview_agent
from src.modules.execution.application.interfaces.agent_runtime import AgentResponseChunk
from src.modules.execution.domain.exceptions import AgentNotAvailableError
from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo


def _make_active_agent_info(
    *,
    agent_id: int = 1,
    model_id: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0",
) -> ActiveAgentInfo:
    return ActiveAgentInfo(
        id=agent_id, name="test-agent", system_prompt="You are helpful.",
        model_id=model_id, temperature=0.7, max_tokens=2048, top_p=1.0,
    )


def _make_user_dto(*, user_id: int = 1) -> UserDTO:
    return UserDTO(id=user_id, email="test@example.com", name="Test User", role="developer", is_active=True)


@pytest.mark.unit
class TestPreviewAgent:
    """preview_agent 端点单元测试。"""

    @pytest.mark.asyncio
    async def test_preview_success(self) -> None:
        """正常预览返回 AgentPreviewResponse。"""
        mock_querier = AsyncMock()
        mock_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_runtime = AsyncMock()
        mock_runtime.execute.return_value = AgentResponseChunk(
            content="你好! 我是一个 AI 助手。", done=True, input_tokens=10, output_tokens=20,
        )

        result = await preview_agent(
            agent_id=1,
            request=PreviewAgentRequest(prompt="你好"),
            current_user=_make_user_dto(),
            agent_runtime=mock_runtime,
            agent_querier=mock_querier,
        )

        assert result.content == "你好! 我是一个 AI 助手。"
        assert result.model_id == "us.anthropic.claude-haiku-4-5-20251001-v1:0"
        assert result.tokens_input == 10
        assert result.tokens_output == 20
        # 验证 max_turns=1
        call_args = mock_runtime.execute.call_args[0][0]
        assert call_args.max_turns == 1

    @pytest.mark.asyncio
    async def test_preview_agent_not_found_raises(self) -> None:
        """Agent 不存在时抛出 AgentNotAvailableError。"""
        mock_querier = AsyncMock()
        mock_querier.get_active_agent.return_value = None
        mock_runtime = AsyncMock()

        with pytest.raises(AgentNotAvailableError):
            await preview_agent(
                agent_id=999,
                request=PreviewAgentRequest(prompt="你好"),
                current_user=_make_user_dto(),
                agent_runtime=mock_runtime,
                agent_querier=mock_querier,
            )

        mock_runtime.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_preview_agent_not_active_raises(self) -> None:
        """Agent 非 ACTIVE 状态时 get_active_agent 返回 None, 抛出 AgentNotAvailableError。"""
        mock_querier = AsyncMock()
        mock_querier.get_active_agent.return_value = None
        mock_runtime = AsyncMock()

        with pytest.raises(AgentNotAvailableError):
            await preview_agent(
                agent_id=1,
                request=PreviewAgentRequest(prompt="你好"),
                current_user=_make_user_dto(),
                agent_runtime=mock_runtime,
                agent_querier=mock_querier,
            )

        mock_runtime.execute.assert_not_called()
