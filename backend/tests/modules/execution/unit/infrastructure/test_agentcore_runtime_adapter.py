"""AgentCoreRuntimeAdapter 单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.execution.application.interfaces import (
    AgentRequest,
    AgentResponseChunk,
    IAgentRuntime,
)
from src.modules.execution.infrastructure.external.agentcore_runtime_adapter import (
    AgentCoreRuntimeAdapter,
)
from src.shared.domain.exceptions import DomainError


# -- 测试辅助 --


def _make_request(**overrides) -> AgentRequest:
    defaults = {"prompt": "你好"}
    defaults.update(overrides)
    return AgentRequest(**defaults)


def _make_invoke_agent_response(text: str) -> dict:
    """构建 invoke_inline_agent 的模拟响应（EventStream 格式）。"""
    return {
        "completion": [
            {"chunk": {"bytes": text.encode("utf-8")}},
        ],
    }


def _make_streaming_events(chunks: list[str]) -> list[dict]:
    """构建流式 EventStream 事件列表。"""
    return [{"chunk": {"bytes": c.encode("utf-8")}} for c in chunks]


# -- 结构测试 --


@pytest.mark.unit
class TestAgentCoreRuntimeAdapterStructure:
    def test_implements_iagent_runtime(self):
        assert issubclass(AgentCoreRuntimeAdapter, IAgentRuntime)

    def test_can_instantiate(self):
        mock_client = MagicMock()
        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        assert adapter is not None


# -- execute() 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestAgentCoreRuntimeAdapterExecute:
    async def test_execute_normal_response(self):
        """正常响应: 收集所有 chunk 拼接为完整内容。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.return_value = {
            "completion": [
                {"chunk": {"bytes": b"\xe4\xbd\xa0\xe5\xa5\xbd"}},  # "你好"
                {"chunk": {"bytes": "！有什么可以帮助你？".encode()}},
            ],
        }

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        result = await adapter.execute(_make_request())

        assert isinstance(result, AgentResponseChunk)
        assert result.content == "你好！有什么可以帮助你？"
        assert result.done is True
        mock_client.invoke_inline_agent.assert_called_once()

    async def test_execute_empty_response(self):
        """空响应: completion 无 chunk 事件。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.return_value = {
            "completion": [],
        }

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        result = await adapter.execute(_make_request())

        assert result.content == ""
        assert result.done is True

    async def test_execute_skips_non_chunk_events(self):
        """非 chunk 事件被忽略。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.return_value = {
            "completion": [
                {"chunk": {"bytes": "内容".encode()}},
                {"trace": {"agentTrace": {}}},  # trace 事件，应被忽略
                {"returnControl": {}},  # returnControl 事件，应被忽略
            ],
        }

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        result = await adapter.execute(_make_request())

        assert result.content == "内容"
        assert result.done is True

    async def test_execute_boto3_exception_raises_domain_error(self):
        """boto3 异常转换为 DomainError。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.side_effect = Exception("Service unavailable")

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        with pytest.raises(DomainError, match="Agent 服务暂时不可用") as exc_info:
            await adapter.execute(_make_request())

        assert exc_info.value.code == "AGENTCORE_RUNTIME_ERROR"

    async def test_execute_domain_error_passthrough(self):
        """DomainError 直接透传，不被二次包装。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.side_effect = DomainError(
            message="配额超限", code="QUOTA_EXCEEDED",
        )

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        with pytest.raises(DomainError, match="配额超限") as exc_info:
            await adapter.execute(_make_request())

        assert exc_info.value.code == "QUOTA_EXCEEDED"

    async def test_execute_passes_request_params(self):
        """验证请求参数正确传递到 boto3 调用。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.return_value = {"completion": []}

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        request = _make_request(
            prompt="测试提示词",
            system_prompt="你是助手",
            model_id="us.anthropic.claude-sonnet-4-6-20260819-v1:0",
        )
        await adapter.execute(request)

        call_kwargs = mock_client.invoke_inline_agent.call_args.kwargs
        # 验证关键参数
        assert call_kwargs["inputText"] == "测试提示词"
        assert call_kwargs["foundationModel"] == "us.anthropic.claude-sonnet-4-6-20260819-v1:0"
        assert call_kwargs["instruction"] == "你是助手"

    async def test_execute_uses_default_model_when_empty(self):
        """model_id 为空时使用默认模型。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.return_value = {"completion": []}

        adapter = AgentCoreRuntimeAdapter(
            client=mock_client,
            default_model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        )
        request = _make_request(model_id="")
        await adapter.execute(request)

        call_kwargs = mock_client.invoke_inline_agent.call_args.kwargs
        assert call_kwargs["foundationModel"] == "us.anthropic.claude-haiku-4-5-20251001-v1:0"


# -- execute_stream() 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestAgentCoreRuntimeAdapterExecuteStream:
    async def test_stream_multi_chunk_response(self):
        """流式响应: 逐 chunk yield。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.return_value = {
            "completion": [
                {"chunk": {"bytes": "第一段".encode()}},
                {"chunk": {"bytes": "第二段".encode()}},
            ],
        }

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        chunks = []
        async for chunk in await adapter.execute_stream(_make_request()):
            chunks.append(chunk)

        # 2 个内容 chunk + 1 个 done chunk
        assert len(chunks) == 3
        assert chunks[0].content == "第一段"
        assert chunks[0].done is False
        assert chunks[1].content == "第二段"
        assert chunks[1].done is False
        assert chunks[2].done is True

    async def test_stream_empty_response(self):
        """空流式响应: 只有 done chunk。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.return_value = {"completion": []}

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        chunks = []
        async for chunk in await adapter.execute_stream(_make_request()):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].done is True

    async def test_stream_boto3_exception_raises_domain_error(self):
        """流式调用 boto3 异常转换为 DomainError。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.side_effect = ConnectionError("网络中断")

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        with pytest.raises(DomainError, match="Agent 服务暂时不可用"):
            async for _ in await adapter.execute_stream(_make_request()):
                pass

    async def test_stream_skips_non_chunk_events(self):
        """流式响应忽略非 chunk 事件。"""
        mock_client = MagicMock()
        mock_client.invoke_inline_agent.return_value = {
            "completion": [
                {"chunk": {"bytes": "内容".encode()}},
                {"trace": {"agentTrace": {}}},
            ],
        }

        adapter = AgentCoreRuntimeAdapter(client=mock_client)
        chunks = []
        async for chunk in await adapter.execute_stream(_make_request()):
            chunks.append(chunk)

        # 1 个内容 chunk + 1 个 done chunk
        assert len(chunks) == 2
        assert chunks[0].content == "内容"
        assert chunks[1].done is True


# -- 配置切换测试 --


@pytest.mark.unit
class TestAgentRuntimeModeSwitch:
    """测试 AGENT_RUNTIME_MODE 配置切换逻辑。"""

    @patch(
        "src.modules.execution.api.dependencies.get_settings",
    )
    def test_in_process_mode_returns_claude_agent_adapter(self, mock_get_settings):
        """in_process 模式返回 ClaudeAgentAdapter。"""
        from src.modules.execution.api.dependencies import get_agent_runtime
        from src.modules.execution.infrastructure.external.claude_agent_adapter import (
            ClaudeAgentAdapter,
        )

        mock_settings = MagicMock()
        mock_settings.AGENT_RUNTIME_MODE = "in_process"
        mock_settings.AWS_REGION = "us-east-1"
        mock_settings.AGENTCORE_MEMORY_ID = ""
        mock_settings.BEDROCK_DEFAULT_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
        mock_get_settings.return_value = mock_settings

        # 清除 lru_cache
        get_agent_runtime.cache_clear()
        runtime = get_agent_runtime()

        assert isinstance(runtime, ClaudeAgentAdapter)
        get_agent_runtime.cache_clear()

    @patch(
        "src.modules.execution.api.dependencies.get_settings",
    )
    def test_agentcore_runtime_mode_returns_agentcore_adapter(self, mock_get_settings):
        """agentcore_runtime 模式返回 AgentCoreRuntimeAdapter。"""
        from src.modules.execution.api.dependencies import get_agent_runtime

        mock_settings = MagicMock()
        mock_settings.AGENT_RUNTIME_MODE = "agentcore_runtime"
        mock_settings.AWS_REGION = "us-east-1"
        mock_settings.AGENTCORE_MEMORY_ID = ""
        mock_settings.BEDROCK_DEFAULT_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
        mock_get_settings.return_value = mock_settings

        get_agent_runtime.cache_clear()
        with patch("boto3.client") as mock_boto3_client:
            runtime = get_agent_runtime()

        assert isinstance(runtime, AgentCoreRuntimeAdapter)
        get_agent_runtime.cache_clear()

    @patch(
        "src.modules.execution.api.dependencies.get_settings",
    )
    def test_default_mode_is_in_process(self, mock_get_settings):
        """默认模式为 in_process。"""
        from src.shared.infrastructure.settings import Settings

        settings = Settings(_env_file=None)
        assert settings.AGENT_RUNTIME_MODE == "in_process"
