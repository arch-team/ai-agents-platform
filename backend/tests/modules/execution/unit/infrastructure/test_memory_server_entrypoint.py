"""Memory MCP Server 入口点单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.execution.application.interfaces import MemoryItem
from src.modules.execution.infrastructure.external.memory_adapter import MemoryAdapter
from src.modules.execution.infrastructure.external.memory_server_entrypoint import (
    TOOLS,
    _handle_initialize,
    _handle_tools_list,
    _make_error,
    _make_response,
    handle_message,
)


# -- JSON-RPC 辅助函数测试 --


@pytest.mark.unit
class TestJsonRpcHelpers:
    """JSON-RPC 响应构建辅助函数测试。"""

    def test_make_response_structure(self) -> None:
        result = _make_response(1, {"key": "value"})
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert result["result"] == {"key": "value"}

    def test_make_response_with_string_id(self) -> None:
        result = _make_response("req-abc", {"ok": True})
        assert result["id"] == "req-abc"

    def test_make_error_structure(self) -> None:
        result = _make_error(2, -32601, "未知方法")
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 2
        assert result["error"]["code"] == -32601
        assert result["error"]["message"] == "未知方法"


# -- initialize 请求测试 --


@pytest.mark.unit
class TestHandleInitialize:
    """initialize 请求处理测试。"""

    def test_returns_protocol_version(self) -> None:
        result = _handle_initialize(1)
        assert result["result"]["protocolVersion"] == "2024-11-05"

    def test_returns_server_info(self) -> None:
        result = _handle_initialize(1)
        info = result["result"]["serverInfo"]
        assert info["name"] == "agentcore-memory"
        assert "version" in info

    def test_returns_tools_capability(self) -> None:
        result = _handle_initialize(1)
        assert "tools" in result["result"]["capabilities"]


# -- tools/list 请求测试 --


@pytest.mark.unit
class TestHandleToolsList:
    """tools/list 请求处理测试。"""

    def test_returns_two_tools(self) -> None:
        result = _handle_tools_list(1)
        tools = result["result"]["tools"]
        assert len(tools) == 2

    def test_tool_names(self) -> None:
        result = _handle_tools_list(1)
        names = [t["name"] for t in result["result"]["tools"]]
        assert "save_memory" in names
        assert "recall_memory" in names

    def test_tools_have_input_schema(self) -> None:
        for tool in TOOLS:
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"


# -- tools/call 请求测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestHandleToolsCall:
    """tools/call 请求处理测试 (通过 handle_message 分发)。"""

    async def test_save_memory_success(self) -> None:
        adapter = AsyncMock(spec=MemoryAdapter)
        adapter.save_memory.return_value = "mem-new-123"

        msg = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "save_memory",
                "arguments": {
                    "agent_id": 42,
                    "content": "用户偏好简洁回复",
                    "topic": "偏好",
                },
            },
        }
        result = await handle_message(msg, adapter)

        assert result is not None
        assert result["id"] == 10
        text = result["result"]["content"][0]["text"]
        assert text == "mem-new-123"
        adapter.save_memory.assert_awaited_once_with(
            agent_id=42,
            content="用户偏好简洁回复",
            topic="偏好",
        )

    async def test_save_memory_noop_returns_skip_marker(self) -> None:
        adapter = AsyncMock(spec=MemoryAdapter)
        adapter.save_memory.return_value = ""

        msg = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "save_memory",
                "arguments": {"agent_id": 1, "content": "c", "topic": "t"},
            },
        }
        result = await handle_message(msg, adapter)

        assert result is not None
        text = result["result"]["content"][0]["text"]
        assert text == "memory_save_skipped"

    async def test_recall_memory_success(self) -> None:
        adapter = AsyncMock(spec=MemoryAdapter)
        adapter.recall_memory.return_value = [
            MemoryItem(
                memory_id="mem-1",
                content="用户喜欢简洁回复",
                topic="偏好",
                relevance_score=0.95,
            ),
        ]

        msg = {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/call",
            "params": {
                "name": "recall_memory",
                "arguments": {"agent_id": 42, "query": "偏好"},
            },
        }
        result = await handle_message(msg, adapter)

        assert result is not None
        assert result["id"] == 20
        import json

        items = json.loads(result["result"]["content"][0]["text"])
        assert len(items) == 1
        assert items[0]["memory_id"] == "mem-1"
        assert items[0]["relevance_score"] == 0.95

    async def test_recall_memory_with_max_results(self) -> None:
        adapter = AsyncMock(spec=MemoryAdapter)
        adapter.recall_memory.return_value = []

        msg = {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "tools/call",
            "params": {
                "name": "recall_memory",
                "arguments": {"agent_id": 1, "query": "q", "max_results": 10},
            },
        }
        await handle_message(msg, adapter)

        adapter.recall_memory.assert_awaited_once_with(
            agent_id=1,
            query="q",
            max_results=10,
        )

    async def test_unknown_tool_returns_error(self) -> None:
        adapter = AsyncMock(spec=MemoryAdapter)

        msg = {
            "jsonrpc": "2.0",
            "id": 30,
            "method": "tools/call",
            "params": {"name": "unknown_tool", "arguments": {}},
        }
        result = await handle_message(msg, adapter)

        assert result is not None
        assert "error" in result
        assert result["error"]["code"] == -32601


# -- handle_message 分发测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestHandleMessage:
    """handle_message 消息分发测试。"""

    async def test_initialize_dispatches(self) -> None:
        adapter = AsyncMock(spec=MemoryAdapter)
        msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        result = await handle_message(msg, adapter)

        assert result is not None
        assert "protocolVersion" in result["result"]

    async def test_tools_list_dispatches(self) -> None:
        adapter = AsyncMock(spec=MemoryAdapter)
        msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        result = await handle_message(msg, adapter)

        assert result is not None
        assert "tools" in result["result"]

    async def test_notification_returns_none(self) -> None:
        adapter = AsyncMock(spec=MemoryAdapter)
        msg = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        result = await handle_message(msg, adapter)

        assert result is None

    async def test_unknown_method_returns_error(self) -> None:
        adapter = AsyncMock(spec=MemoryAdapter)
        msg = {"jsonrpc": "2.0", "id": 99, "method": "unknown/method", "params": {}}
        result = await handle_message(msg, adapter)

        assert result is not None
        assert "error" in result
        assert result["error"]["code"] == -32601


# -- main 函数测试 --


@pytest.mark.unit
class TestMain:
    """main 入口函数测试。"""

    @patch.dict("os.environ", {"AGENTCORE_MEMORY_ID": "mem-test", "AWS_REGION": "us-west-2"})
    @patch(
        "src.modules.execution.infrastructure.external.memory_server_entrypoint.run_stdio_loop",
        new_callable=MagicMock,
    )
    @patch("src.modules.execution.infrastructure.external.memory_server_entrypoint.asyncio")
    @patch("src.modules.execution.infrastructure.external.memory_server_entrypoint.MemoryAdapter")
    def test_main_reads_env_and_creates_adapter(
        self,
        mock_adapter_cls: MagicMock,
        mock_asyncio: MagicMock,
        mock_run_loop: MagicMock,
    ) -> None:
        from src.modules.execution.infrastructure.external.memory_server_entrypoint import main

        main()

        mock_adapter_cls.assert_called_once_with(memory_id="mem-test", region="us-west-2")
        mock_run_loop.assert_called_once_with(mock_adapter_cls.return_value)
        mock_asyncio.run.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    @patch(
        "src.modules.execution.infrastructure.external.memory_server_entrypoint.run_stdio_loop",
        new_callable=MagicMock,
    )
    @patch("src.modules.execution.infrastructure.external.memory_server_entrypoint.asyncio")
    @patch("src.modules.execution.infrastructure.external.memory_server_entrypoint.MemoryAdapter")
    def test_main_defaults_when_env_missing(
        self,
        mock_adapter_cls: MagicMock,
        mock_asyncio: MagicMock,
        mock_run_loop: MagicMock,
    ) -> None:
        from src.modules.execution.infrastructure.external.memory_server_entrypoint import main

        main()

        mock_adapter_cls.assert_called_once_with(memory_id="", region="ap-northeast-1")
        mock_run_loop.assert_called_once_with(mock_adapter_cls.return_value)
        mock_asyncio.run.assert_called_once()
