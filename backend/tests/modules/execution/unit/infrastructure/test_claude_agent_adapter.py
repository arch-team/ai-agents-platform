"""ClaudeAgentAdapter 单元测试。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.execution.application.interfaces import (
    AgentRequest,
    AgentResponseChunk,
    AgentTool,
    IAgentRuntime,
)
from src.modules.execution.infrastructure.external.claude_agent_adapter import (
    ClaudeAgentAdapter,
)
from src.modules.execution.infrastructure.external.sdk_message_utils import (
    extract_content,
    extract_usage,
)
from src.shared.domain.exceptions import DomainError


# -- 测试辅助 --


def _make_request(**overrides) -> AgentRequest:
    defaults = {"prompt": "你好"}
    defaults.update(overrides)
    return AgentRequest(**defaults)


def _make_tool(name: str = "search", tool_type: str = "mcp_server", **kwargs) -> AgentTool:
    defaults = {
        "name": name,
        "description": f"{name} 工具",
        "input_schema": {"type": "object"},
        "tool_type": tool_type,
    }
    defaults.update(kwargs)
    return AgentTool(**defaults)


async def _async_iter(items):
    for item in items:
        yield item


# -- 结构测试 --


@pytest.mark.unit
class TestClaudeAgentAdapterStructure:
    def test_implements_iagent_runtime(self):
        assert issubclass(ClaudeAgentAdapter, IAgentRuntime)

    def test_can_instantiate(self):
        adapter = ClaudeAgentAdapter()
        assert adapter is not None


# -- execute() 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestClaudeAgentAdapterExecute:
    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_execute_normal_response(self, mock_query):
        mock_query.return_value = _async_iter(
            [
                {"type": "text", "content": "你好！"},
                {"type": "text", "content": "有什么可以帮助你？", "usage": {"input_tokens": 10, "output_tokens": 20}},
            ],
        )

        adapter = ClaudeAgentAdapter()
        result = await adapter.execute(_make_request())

        assert isinstance(result, AgentResponseChunk)
        assert result.content == "你好！有什么可以帮助你？"
        assert result.done is True
        assert result.input_tokens == 10
        assert result.output_tokens == 20
        mock_query.assert_called_once()

    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_execute_empty_response(self, mock_query):
        mock_query.return_value = _async_iter([])

        adapter = ClaudeAgentAdapter()
        result = await adapter.execute(_make_request())

        assert result.content == ""
        assert result.done is True
        assert result.input_tokens == 0
        assert result.output_tokens == 0

    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_execute_sdk_exception_raises_domain_error(self, mock_query):
        mock_query.return_value = _async_iter([])

        async def _raise_error(*args, **kwargs):
            raise RuntimeError("SDK 连接失败")
            yield  # - 使其成为异步生成器

        mock_query.return_value = _raise_error()

        adapter = ClaudeAgentAdapter()
        with pytest.raises(DomainError, match="Agent 服务暂时不可用") as exc_info:
            await adapter.execute(_make_request())

        assert exc_info.value.code == "AGENT_SDK_ERROR"

    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_execute_domain_error_passthrough(self, mock_query):
        async def _raise_domain_error(*args, **kwargs):
            raise DomainError(message="配额超限", code="QUOTA_EXCEEDED")
            yield

        mock_query.return_value = _raise_domain_error()

        adapter = ClaudeAgentAdapter()
        with pytest.raises(DomainError, match="配额超限") as exc_info:
            await adapter.execute(_make_request())

        assert exc_info.value.code == "QUOTA_EXCEEDED"

    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_execute_string_message(self, mock_query):
        mock_query.return_value = _async_iter(["纯文本响应"])

        adapter = ClaudeAgentAdapter()
        result = await adapter.execute(_make_request())

        assert result.content == "纯文本响应"
        assert result.done is True

    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_execute_dict_with_content_key(self, mock_query):
        mock_query.return_value = _async_iter([{"content": "备选格式"}])

        adapter = ClaudeAgentAdapter()
        result = await adapter.execute(_make_request())

        assert result.content == "备选格式"

    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_execute_passes_options(self, mock_query):
        mock_query.return_value = _async_iter([])

        adapter = ClaudeAgentAdapter()
        request = _make_request(
            system_prompt="你是助手",
            model_id="claude-sonnet-4-20250514",
            max_turns=5,
            cwd="/tmp/workspace",
        )
        await adapter.execute(request)

        call_kwargs = mock_query.call_args
        assert call_kwargs.kwargs["prompt"] == "你好"
        options = call_kwargs.kwargs["options"]
        assert options.system_prompt == "你是助手"
        assert options.model == "claude-sonnet-4-20250514"
        assert options.max_turns == 5
        assert options.cwd == "/tmp/workspace"
        assert options.permission_mode == "bypassPermissions"


# -- execute_stream() 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestClaudeAgentAdapterExecuteStream:
    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_stream_multi_chunk_response(self, mock_query):
        mock_query.return_value = _async_iter(
            [
                {"type": "text", "content": "第一段"},
                {"type": "text", "content": "第二段", "usage": {"input_tokens": 5, "output_tokens": 15}},
            ],
        )

        adapter = ClaudeAgentAdapter()
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
        assert chunks[2].input_tokens == 5
        assert chunks[2].output_tokens == 15

    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_stream_empty_response(self, mock_query):
        mock_query.return_value = _async_iter([])

        adapter = ClaudeAgentAdapter()
        chunks = []
        async for chunk in await adapter.execute_stream(_make_request()):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].done is True
        assert chunks[0].input_tokens == 0

    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_stream_sdk_exception_raises_domain_error(self, mock_query):
        async def _raise_error(*args, **kwargs):
            raise ConnectionError("网络中断")
            yield

        mock_query.return_value = _raise_error()

        adapter = ClaudeAgentAdapter()
        with pytest.raises(DomainError, match="Agent 服务暂时不可用"):
            async for _ in await adapter.execute_stream(_make_request()):
                pass

    @patch("src.modules.execution.infrastructure.external.claude_agent_adapter.query")
    async def test_stream_accumulates_usage(self, mock_query):
        mock_query.return_value = _async_iter(
            [
                {"type": "text", "content": "A", "usage": {"input_tokens": 3, "output_tokens": 5}},
                {"type": "text", "content": "B", "usage": {"input_tokens": 2, "output_tokens": 4}},
            ],
        )

        adapter = ClaudeAgentAdapter()
        chunks = []
        async for chunk in await adapter.execute_stream(_make_request()):
            chunks.append(chunk)

        done_chunk = chunks[-1]
        assert done_chunk.done is True
        assert done_chunk.input_tokens == 5
        assert done_chunk.output_tokens == 9


# -- _build_mcp_config() 测试 --


@pytest.mark.unit
class TestBuildMcpConfig:
    def test_no_tools_returns_empty(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request()
        result = adapter._build_mcp_config(request)
        assert result == {}

    def test_mcp_tools_with_gateway_url_and_auth(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[_make_tool("search", "mcp_server")],
            gateway_url="https://gateway.example.com/mcp",
            gateway_auth_token="test-token",
        )
        result = adapter._build_mcp_config(request)

        assert "gateway" in result
        assert result["gateway"]["type"] == "sse"
        assert result["gateway"]["url"] == "https://gateway.example.com/mcp"
        assert result["gateway"]["requestInit"]["headers"]["Authorization"] == "Bearer test-token"

    def test_mcp_tools_with_gateway_url_but_no_auth_skips(self):
        """无 auth_token 时跳过 gateway, 避免 CLI 401 崩溃。"""
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[_make_tool("search", "mcp_server")],
            gateway_url="https://gateway.example.com/mcp",
        )
        result = adapter._build_mcp_config(request)

        assert "gateway" not in result

    def test_mcp_tools_without_gateway_url_no_gateway_config(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[_make_tool("search", "mcp_server")],
            gateway_url="",
        )
        result = adapter._build_mcp_config(request)

        assert "gateway" not in result

    def test_api_tools_create_platform_tools_config(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[_make_tool("calculator", "api")],
        )
        result = adapter._build_mcp_config(request)

        assert "platform-tools" in result
        config = result["platform-tools"]
        assert config["type"] == "sdk"
        assert config["name"] == "platform-tools"

    def test_function_tools_create_platform_tools_config(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[_make_tool("validator", "function")],
        )
        result = adapter._build_mcp_config(request)

        assert "platform-tools" in result
        assert result["platform-tools"]["type"] == "sdk"

    def test_mixed_tools_create_both_configs(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[
                _make_tool("search", "mcp_server"),
                _make_tool("calculator", "api"),
            ],
            gateway_url="https://gw.example.com",
            gateway_auth_token="test-token",
        )
        result = adapter._build_mcp_config(request)

        assert "gateway" in result
        assert "platform-tools" in result


# -- _build_allowed_tools() 测试 --


@pytest.mark.unit
class TestBuildAllowedTools:
    def test_empty_tools(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request()
        result = adapter._build_allowed_tools(request)
        assert result == []

    def test_mcp_server_tool(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[_make_tool("search", "mcp_server")],
        )
        result = adapter._build_allowed_tools(request)

        assert result == ["mcp__gateway__search"]

    def test_api_tool(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[_make_tool("calculator", "api")],
        )
        result = adapter._build_allowed_tools(request)

        assert result == ["mcp__platform-tools__calculator"]

    def test_function_tool(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[_make_tool("validator", "function")],
        )
        result = adapter._build_allowed_tools(request)

        assert result == ["mcp__platform-tools__validator"]

    def test_mixed_tools(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            tools=[
                _make_tool("search", "mcp_server"),
                _make_tool("calc", "api"),
                _make_tool("check", "function"),
            ],
        )
        result = adapter._build_allowed_tools(request)

        assert result == [
            "mcp__gateway__search",
            "mcp__platform-tools__calc",
            "mcp__platform-tools__check",
        ]


# -- _extract_content() / _extract_usage() 测试 --


@pytest.mark.unit
class TestExtractHelpers:
    def test_extract_content_text_type(self):
        msg = {"type": "text", "content": "内容"}
        assert extract_content(msg) == "内容"

    def test_extract_content_dict_with_content_key(self):
        msg = {"content": "备选"}
        assert extract_content(msg) == "备选"

    def test_extract_content_string(self):
        assert extract_content("纯文本") == "纯文本"

    def test_extract_content_unknown_type(self):
        assert extract_content(42) == ""

    def test_extract_content_tool_use_type(self):
        msg = {"type": "tool_use", "name": "search"}
        assert extract_content(msg) == ""

    def test_extract_usage_with_usage(self):
        msg = {"usage": {"input_tokens": 10, "output_tokens": 20}}
        assert extract_usage(msg) == (10, 20)

    def test_extract_usage_no_usage(self):
        msg = {"type": "text", "content": "无 usage"}
        assert extract_usage(msg) == (0, 0)

    def test_extract_usage_non_dict(self):
        assert extract_usage("字符串") == (0, 0)

    def test_extract_usage_partial_usage(self):
        msg = {"usage": {"input_tokens": 5}}
        assert extract_usage(msg) == (5, 0)


# -- _build_options() 测试 --


@pytest.mark.unit
class TestBuildOptions:
    def test_minimal_request(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request()
        options = adapter._build_options(request)

        assert options.permission_mode == "bypassPermissions"

    def test_full_request(self):
        adapter = ClaudeAgentAdapter()
        request = _make_request(
            system_prompt="你是助手",
            model_id="claude-sonnet-4-20250514",
            max_turns=10,
            cwd="/workspace",
            tools=[_make_tool("search", "mcp_server")],
            gateway_url="https://gw.example.com",
        )
        options = adapter._build_options(request)

        assert options.system_prompt == "你是助手"
        assert options.model == "claude-sonnet-4-20250514"
        assert options.max_turns == 10
        assert options.cwd == "/workspace"
        assert options.permission_mode == "bypassPermissions"
        assert options.mcp_servers is not None
        assert options.allowed_tools is not None


@pytest.mark.unit
class TestMemoryMcpIntegration:
    """Memory MCP Server 集成测试。"""

    def test_memory_config_added_when_memory_id_set(self) -> None:
        adapter = ClaudeAgentAdapter(memory_id="mem-test-123", region="us-east-1")
        request = _make_request()
        config = adapter._build_mcp_config(request)
        assert "memory" in config
        assert config["memory"]["type"] == "stdio"
        assert config["memory"]["env"]["AGENTCORE_MEMORY_ID"] == "mem-test-123"

    def test_no_memory_config_when_memory_id_empty(self) -> None:
        adapter = ClaudeAgentAdapter(memory_id="", region="us-east-1")
        request = _make_request()
        config = adapter._build_mcp_config(request)
        assert "memory" not in config

    def test_memory_tools_in_allowed_list_when_memory_id_set(self) -> None:
        adapter = ClaudeAgentAdapter(memory_id="mem-abc", region="us-east-1")
        request = _make_request()
        allowed = adapter._build_allowed_tools(request)
        assert "mcp__memory__save_memory" in allowed
        assert "mcp__memory__recall_memory" in allowed

    def test_no_memory_tools_when_memory_id_empty(self) -> None:
        adapter = ClaudeAgentAdapter(memory_id="", region="us-east-1")
        request = _make_request()
        allowed = adapter._build_allowed_tools(request)
        assert "mcp__memory__save_memory" not in allowed
        assert "mcp__memory__recall_memory" not in allowed

    def test_memory_coexists_with_gateway_and_platform_tools(self) -> None:
        adapter = ClaudeAgentAdapter(memory_id="mem-xyz", region="ap-northeast-1")
        request = _make_request(
            tools=[
                _make_tool("web-search", "mcp_server"),
                _make_tool("http-call", "api"),
            ],
            gateway_url="https://gw.example.com",
            gateway_auth_token="test-token",
        )
        config = adapter._build_mcp_config(request)
        assert "gateway" in config
        assert "platform-tools" in config
        assert "memory" in config


# -- _create_tool_handler() / _call_api_tool() 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestToolHandler:
    async def test_function_tool_handler_returns_summary(self) -> None:
        tool = _make_tool("my-func", "function")
        handler = ClaudeAgentAdapter._create_tool_handler(tool)
        result = await handler({"key": "value"})

        assert len(result["content"]) == 1
        assert "my-func" in result["content"][0]["text"]
        assert "key" in result["content"][0]["text"]

    async def test_api_tool_without_endpoint_returns_summary(self) -> None:
        tool = _make_tool("no-endpoint", "api", config={})
        handler = ClaudeAgentAdapter._create_tool_handler(tool)
        result = await handler({"x": 1})

        assert "no-endpoint" in result["content"][0]["text"]

    @patch("httpx.AsyncClient")
    async def test_api_tool_with_endpoint_calls_http(self, mock_client_cls) -> None:
        mock_resp = AsyncMock()
        mock_resp.text = '{"result": 42}'
        mock_resp.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        config = {"endpoint_url": "https://api.example.com/calc", "method": "POST"}
        result = await ClaudeAgentAdapter._call_api_tool(config, {"a": 1})

        assert result["content"][0]["text"] == '{"result": 42}'
        mock_client.request.assert_called_once()

    @patch("httpx.AsyncClient")
    async def test_api_tool_http_error_returns_error_message(self, mock_client_cls) -> None:
        import httpx

        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.HTTPError("连接超时")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        config = {"endpoint_url": "https://api.example.com/fail", "method": "POST"}
        result = await ClaudeAgentAdapter._call_api_tool(config, {})

        assert "API 调用失败" in result["content"][0]["text"]
