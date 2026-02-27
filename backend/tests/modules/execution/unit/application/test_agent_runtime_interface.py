"""IAgentRuntime 接口测试。"""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest

from src.modules.execution.application.interfaces import (
    AgentRequest,
    AgentResponseChunk,
    AgentTool,
    IAgentRuntime,
)


@pytest.mark.unit
class TestAgentRuntimeDataStructures:
    """Agent 运行时数据结构测试。"""

    def test_agent_tool_creation(self) -> None:
        tool = AgentTool(
            name="search",
            description="搜索工具",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
            tool_type="mcp_server",
            config={"server_url": "http://example.com"},
        )
        assert tool.name == "search"
        assert tool.tool_type == "mcp_server"
        assert tool.config["server_url"] == "http://example.com"

    def test_agent_request_defaults(self) -> None:
        request = AgentRequest(prompt="Hello")
        assert request.prompt == "Hello"
        assert request.system_prompt == ""
        assert request.tools == []
        assert request.history == []
        assert request.temperature == 0.7
        assert request.max_tokens == 2048
        assert request.gateway_url == ""
        assert request.max_turns == 20

    def test_agent_request_with_tools(self) -> None:
        tool = AgentTool(name="t1", description="d1", input_schema={}, tool_type="api")
        request = AgentRequest(
            prompt="分析代码",
            system_prompt="你是代码审查专家",
            model_id="anthropic.claude-sonnet",
            tools=[tool],
            gateway_url="http://gateway.example.com",
        )
        assert len(request.tools) == 1
        assert request.model_id == "anthropic.claude-sonnet"

    def test_agent_response_chunk_defaults(self) -> None:
        chunk = AgentResponseChunk()
        assert chunk.content == ""
        assert chunk.tool_use is None
        assert chunk.tool_result is None
        assert chunk.done is False

    def test_agent_response_chunk_done(self) -> None:
        chunk = AgentResponseChunk(
            content="完成",
            done=True,
            input_tokens=100,
            output_tokens=200,
        )
        assert chunk.done is True
        assert chunk.input_tokens == 100


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestAgentRuntimeMock:
    """IAgentRuntime Mock 测试。"""

    async def test_mock_agent_runtime_execute(self) -> None:
        mock_runtime = AsyncMock(spec=IAgentRuntime)
        mock_runtime.execute.return_value = AgentResponseChunk(
            content="修复完成",
            done=True,
            input_tokens=50,
            output_tokens=100,
        )

        request = AgentRequest(prompt="修复 bug")
        result = await mock_runtime.execute(request)

        assert result.content == "修复完成"
        assert result.done is True
        mock_runtime.execute.assert_called_once_with(request)

    async def test_mock_agent_runtime_execute_stream(self) -> None:
        chunks = [
            AgentResponseChunk(content="正在"),
            AgentResponseChunk(content="分析"),
            AgentResponseChunk(content="...", done=True, input_tokens=30, output_tokens=60),
        ]

        mock_runtime = AsyncMock(spec=IAgentRuntime)

        async def _gen() -> AsyncIterator[AgentResponseChunk]:
            for c in chunks:
                yield c

        mock_runtime.execute_stream.return_value = _gen()

        request = AgentRequest(prompt="分析代码")
        collected = []
        stream = await mock_runtime.execute_stream(request)
        async for chunk in stream:
            collected.append(chunk)

        assert len(collected) == 3
        assert collected[-1].done is True
