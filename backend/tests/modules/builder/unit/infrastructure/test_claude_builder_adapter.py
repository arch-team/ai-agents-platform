"""ClaudeBuilderAdapter 单元测试 — SDK 薄封装。"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.builder.application.interfaces.builder_llm_service import (
    BuilderMessage,
    PlatformContext,
    PlatformSkillInfo,
    PlatformToolInfo,
)
from src.modules.builder.infrastructure.external.claude_builder_adapter import ClaudeBuilderAdapter
from src.shared.domain.exceptions import DomainError


def _mock_result_message(result_text: str) -> MagicMock:
    """创建模拟的 ResultMessage。"""
    from claude_agent_sdk.types import ResultMessage

    msg = MagicMock(spec=ResultMessage)
    msg.result = result_text
    return msg


@pytest.fixture
def adapter() -> ClaudeBuilderAdapter:
    return ClaudeBuilderAdapter()


@pytest.mark.unit
class TestGenerateBlueprint:
    """V2 Blueprint 生成。"""

    @pytest.mark.asyncio
    async def test_generate_blueprint_with_messages(self, adapter: ClaudeBuilderAdapter) -> None:
        mock_msg = _mock_result_message("```yaml\npersona:\n  role: 客服\n```")

        async def mock_query(**kwargs: object):
            yield mock_msg

        messages = [
            BuilderMessage(role="user", content="我想创建一个客服 Agent"),
            BuilderMessage(role="assistant", content="好的，请问您需要什么功能?"),
            BuilderMessage(role="user", content="需要处理退货"),
        ]
        ctx = PlatformContext(
            available_tools=[PlatformToolInfo(id=1, name="订单查询", description="查询")],
            available_skills=[
                PlatformSkillInfo(id=2, name="退货处理", description="退货", category="customer_service"),
            ],
        )

        with patch("src.modules.builder.infrastructure.external.claude_builder_adapter.query", side_effect=mock_query):
            chunks: list[str] = []
            async for chunk in adapter.generate_blueprint(messages, platform_context=ctx):
                chunks.append(chunk)

        assert len(chunks) == 1

    @pytest.mark.asyncio
    async def test_generate_blueprint_without_context(self, adapter: ClaudeBuilderAdapter) -> None:
        mock_msg = _mock_result_message("response")

        async def mock_query(**kwargs: object):
            yield mock_msg

        messages = [BuilderMessage(role="user", content="Hello")]

        with patch("src.modules.builder.infrastructure.external.claude_builder_adapter.query", side_effect=mock_query):
            chunks: list[str] = []
            async for chunk in adapter.generate_blueprint(messages):
                chunks.append(chunk)

        assert len(chunks) == 1


@pytest.mark.unit
class TestCallSdkErrorHandling:
    """SDK 调用错误处理。"""

    @pytest.mark.asyncio
    async def test_sdk_exception_raises_domain_error(self, adapter: ClaudeBuilderAdapter) -> None:
        async def mock_query_error(**kwargs: object):
            raise RuntimeError("SDK 连接失败")
            yield

        with (
            patch(
                "src.modules.builder.infrastructure.external.claude_builder_adapter.query",
                side_effect=mock_query_error,
            ),
            pytest.raises(DomainError, match="Agent 配置生成失败"),
        ):
            async for _ in adapter.generate_blueprint([BuilderMessage(role="user", content="test")]):
                pass

    @pytest.mark.asyncio
    async def test_empty_result_returns_empty_string(self, adapter: ClaudeBuilderAdapter) -> None:
        mock_msg = _mock_result_message("")

        async def mock_query(**kwargs: object):
            yield mock_msg

        with patch("src.modules.builder.infrastructure.external.claude_builder_adapter.query", side_effect=mock_query):
            chunks: list[str] = []
            async for chunk in adapter.generate_blueprint([BuilderMessage(role="user", content="test")]):
                chunks.append(chunk)

        assert chunks == [""]

    @pytest.mark.asyncio
    async def test_no_result_message_returns_empty(self, adapter: ClaudeBuilderAdapter) -> None:
        """SDK 返回非 ResultMessage 类型时，结果为空字符串。"""
        non_result = MagicMock()
        non_result.__class__.__name__ = "AssistantMessage"

        async def mock_query(**kwargs: object):
            yield non_result

        with patch("src.modules.builder.infrastructure.external.claude_builder_adapter.query", side_effect=mock_query):
            chunks: list[str] = []
            async for chunk in adapter.generate_blueprint([BuilderMessage(role="user", content="test")]):
                chunks.append(chunk)

        assert chunks == [""]
