"""AgentCoreRuntimeAdapter 单元测试。"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.modules.execution.application.interfaces import (
    AgentRequest,
    AgentResponseChunk,
    AgentTool,
    IAgentRuntime,
)
from src.modules.execution.infrastructure.external.agentcore_runtime_adapter import (
    AgentCoreRuntimeAdapter,
)
from src.shared.domain.exceptions import DomainError


# -- 测试辅助 --

_TEST_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/test-runtime"


def _make_request(**overrides: object) -> AgentRequest:
    defaults: dict[str, object] = {"prompt": "你好"}
    defaults.update(overrides)
    return AgentRequest(**defaults)


def _make_runtime_response(content: str = "你好!", input_tokens: int = 10, output_tokens: int = 20) -> dict:
    """构建 invoke_agent_runtime 的模拟响应 (旧格式 body: JSON string)。"""
    return {
        "body": json.dumps(
            {
                "content": content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        ),
    }


def _make_streaming_response(content: str = "你好!", input_tokens: int = 10, output_tokens: int = 20) -> dict:
    """构建 invoke_agent_runtime 的模拟响应 (新 SDK 格式 response: StreamingBody)。"""
    import io

    body_bytes = json.dumps(
        {"content": content, "input_tokens": input_tokens, "output_tokens": output_tokens},
    ).encode("utf-8")
    streaming_body = io.BytesIO(body_bytes)
    return {"response": streaming_body, "statusCode": 200, "runtimeSessionId": "test-session"}


# -- 结构测试 --


@pytest.mark.unit
class TestAgentCoreRuntimeAdapterStructure:
    def test_implements_iagent_runtime(self) -> None:
        assert issubclass(AgentCoreRuntimeAdapter, IAgentRuntime)

    def test_can_instantiate(self) -> None:
        adapter = AgentCoreRuntimeAdapter(client=MagicMock(), runtime_arn=_TEST_RUNTIME_ARN)
        assert adapter is not None


# -- execute() 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestAgentCoreRuntimeAdapterExecute:
    async def test_execute_normal_response(self) -> None:
        """正常响应: 解析 body 中的 content 和 token 统计。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = _make_runtime_response(
            content="你好! 有什么可以帮助你?",
            input_tokens=15,
            output_tokens=25,
        )

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        result = await adapter.execute(_make_request())

        assert isinstance(result, AgentResponseChunk)
        assert result.content == "你好! 有什么可以帮助你?"
        assert result.done is True
        assert result.input_tokens == 15
        assert result.output_tokens == 25
        mock_client.invoke_agent_runtime.assert_called_once()

    async def test_execute_streaming_body_response(self) -> None:
        """新 SDK 格式: 从 response StreamingBody 解析内容。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = _make_streaming_response(
            content="来自 StreamingBody",
            input_tokens=5,
            output_tokens=12,
        )

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        result = await adapter.execute(_make_request())

        assert result.content == "来自 StreamingBody"
        assert result.input_tokens == 5
        assert result.output_tokens == 12

    async def test_execute_empty_response(self) -> None:
        """空响应: content 为空字符串。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = _make_runtime_response(content="")

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        result = await adapter.execute(_make_request())

        assert result.content == ""
        assert result.done is True

    async def test_execute_boto3_exception_raises_domain_error(self) -> None:
        """boto3 异常转换为 DomainError。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.side_effect = Exception("Service unavailable")

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        with pytest.raises(DomainError, match="Agent 服务暂时不可用") as exc_info:
            await adapter.execute(_make_request())

        assert exc_info.value.code == "AGENTCORE_RUNTIME_ERROR"

    async def test_execute_domain_error_passthrough(self) -> None:
        """DomainError 直接透传。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.side_effect = DomainError(message="配额超限", code="QUOTA_EXCEEDED")

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        with pytest.raises(DomainError, match="配额超限") as exc_info:
            await adapter.execute(_make_request())

        assert exc_info.value.code == "QUOTA_EXCEEDED"

    async def test_execute_passes_correct_payload(self) -> None:
        """验证 payload 格式匹配 agent_entrypoint.py 期望。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = _make_runtime_response()

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        request = _make_request(
            prompt="测试提示词",
            system_prompt="你是助手",
            gateway_url="https://gateway.example.com/mcp",
        )
        await adapter.execute(request)

        call_kwargs = mock_client.invoke_agent_runtime.call_args.kwargs
        assert call_kwargs["agentRuntimeArn"] == _TEST_RUNTIME_ARN
        payload = json.loads(call_kwargs["payload"])
        assert payload["prompt"] == "测试提示词"
        assert payload["system_prompt"] == "你是助手"
        assert payload["gateway_url"] == "https://gateway.example.com/mcp"

    async def test_execute_includes_tool_whitelist(self) -> None:
        """工具白名单正确映射到 payload。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = _make_runtime_response()

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        tools = [
            AgentTool(name="weather", description="天气", input_schema={}, tool_type="mcp_server"),
            AgentTool(name="calc", description="计算", input_schema={}, tool_type="api"),
        ]
        request = _make_request(tools=tools)
        await adapter.execute(request)

        payload = json.loads(mock_client.invoke_agent_runtime.call_args.kwargs["payload"])
        assert "mcp__gateway__weather" in payload["allowed_tools"]
        assert "mcp__platform-tools__calc" in payload["allowed_tools"]


# -- execute_stream() 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestAgentCoreRuntimeAdapterExecuteStream:
    async def test_stream_response(self) -> None:
        """流式响应: 1 个内容 chunk + 1 个 done chunk。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = _make_runtime_response(content="回复内容")

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        stream = await adapter.execute_stream(_make_request())
        chunks = [chunk async for chunk in stream]

        assert len(chunks) == 2
        assert chunks[0].content == "回复内容"
        assert chunks[1].done is True

    async def test_stream_empty_response(self) -> None:
        """空流式响应: 只有 done chunk。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = _make_runtime_response(content="")

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        stream = await adapter.execute_stream(_make_request())
        chunks = [chunk async for chunk in stream]

        assert len(chunks) == 1
        assert chunks[0].done is True

    async def test_stream_exception_raises_domain_error(self) -> None:
        """流式调用异常转换为 DomainError。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.side_effect = ConnectionError("网络中断")

        adapter = AgentCoreRuntimeAdapter(client=mock_client, runtime_arn=_TEST_RUNTIME_ARN)
        with pytest.raises(DomainError, match="Agent 服务暂时不可用"):
            stream = await adapter.execute_stream(_make_request())
            async for _ in stream:
                pass


# -- 配置切换测试 --


@pytest.mark.unit
class TestAgentRuntimeModeSwitch:
    """测试 AGENT_RUNTIME_MODE 配置切换逻辑。"""

    @patch("src.modules.execution.api.dependencies.get_settings")
    def test_in_process_mode_returns_claude_agent_adapter(self, mock_get_settings: MagicMock) -> None:
        """in_process 模式返回 ClaudeAgentAdapter。"""
        from src.modules.execution.api.dependencies import get_agent_runtime
        from src.modules.execution.infrastructure.external.claude_agent_adapter import ClaudeAgentAdapter

        mock_settings = MagicMock()
        mock_settings.AGENT_RUNTIME_MODE = "in_process"
        mock_get_settings.return_value = mock_settings

        get_agent_runtime.cache_clear()
        runtime = get_agent_runtime()

        assert isinstance(runtime, ClaudeAgentAdapter)
        get_agent_runtime.cache_clear()

    @patch("src.modules.execution.api.dependencies.get_settings")
    def test_agentcore_runtime_mode_returns_agentcore_adapter(self, mock_get_settings: MagicMock) -> None:
        """agentcore_runtime 模式 + ARN 配置返回 AgentCoreRuntimeAdapter。"""
        from src.modules.execution.api.dependencies import get_agent_runtime

        mock_settings = MagicMock()
        mock_settings.AGENT_RUNTIME_MODE = "agentcore_runtime"
        mock_settings.AWS_REGION = "us-east-1"
        mock_settings.AGENTCORE_RUNTIME_ARN = _TEST_RUNTIME_ARN
        mock_get_settings.return_value = mock_settings

        get_agent_runtime.cache_clear()
        with patch("boto3.client"):
            runtime = get_agent_runtime()

        assert isinstance(runtime, AgentCoreRuntimeAdapter)
        get_agent_runtime.cache_clear()

    @patch("src.modules.execution.api.dependencies.get_settings")
    def test_agentcore_runtime_fallback_when_no_arn(self, mock_get_settings: MagicMock) -> None:
        """agentcore_runtime 模式但 ARN 未配置时降级到 in_process。"""
        from src.modules.execution.api.dependencies import get_agent_runtime
        from src.modules.execution.infrastructure.external.claude_agent_adapter import ClaudeAgentAdapter

        mock_settings = MagicMock()
        mock_settings.AGENT_RUNTIME_MODE = "agentcore_runtime"
        mock_settings.AGENTCORE_RUNTIME_ARN = ""
        mock_get_settings.return_value = mock_settings

        get_agent_runtime.cache_clear()
        runtime = get_agent_runtime()

        assert isinstance(runtime, ClaudeAgentAdapter)
        get_agent_runtime.cache_clear()

    def test_default_mode_is_in_process(self) -> None:
        """默认模式为 in_process。"""
        from src.shared.infrastructure.settings import Settings

        settings = Settings(_env_file=None)
        assert settings.AGENT_RUNTIME_MODE == "in_process"
