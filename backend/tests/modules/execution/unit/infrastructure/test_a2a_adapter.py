"""A2AAdapter 单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.execution.infrastructure.external.a2a_adapter import (
    A2AAdapter,
    A2ATaskResult,
    A2ATaskStatus,
)


# -- NoOp 降级测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestA2AAdapterNoOp:
    """未配置 gateway_url 时的 NoOp 降级行为。"""

    async def test_send_task_returns_skipped(self) -> None:
        adapter = A2AAdapter(gateway_url="", region="us-east-1")
        result = await adapter.send_task(target_agent_url="http://agent", message="hello")
        assert result == A2ATaskResult(task_id="", status="skipped")

    async def test_get_task_status_returns_skipped(self) -> None:
        adapter = A2AAdapter(gateway_url="", region="us-east-1")
        result = await adapter.get_task_status(task_id="task-123")
        assert result == A2ATaskStatus(task_id="task-123", status="skipped")


# -- send_task 成功通信 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestA2AAdapterSendTaskSuccess:
    """send_task 成功通信测试。"""

    async def test_send_task_success(self) -> None:
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = {
            "result": {
                "id": "task-abc",
                "status": {"state": "submitted"},
                "artifacts": [{"parts": [{"type": "text", "text": "ok"}]}],
            },
        }

        adapter = A2AAdapter(gateway_url="https://gw.example.com", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.send_task(
                target_agent_url="http://agent-a",
                message="hello agent",
                session_id="sess-001",
            )
        assert result.task_id == "task-abc"
        assert result.status == "submitted"
        assert result.content == "ok"


# -- send_task JSON-RPC 格式验证 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestA2AAdapterJsonRpcFormat:
    """验证 send_task 构造的 JSON-RPC 载荷格式。"""

    async def test_send_task_jsonrpc_format(self) -> None:
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = {
            "result": {"id": "t-1", "status": {"state": "submitted"}},
        }

        adapter = A2AAdapter(gateway_url="https://gw.example.com", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            await adapter.send_task(target_agent_url="http://target", message="test msg")

        # 检查 invoke_agent_runtime 调用参数中的 payload
        call_kwargs = mock_client.invoke_agent_runtime.call_args[1]
        payload = call_kwargs["payload"]
        assert payload["jsonrpc"] == "2.0"
        assert payload["method"] == "tasks/send"
        assert payload["params"]["message"]["role"] == "user"
        assert payload["params"]["message"]["parts"][0]["type"] == "text"
        assert payload["params"]["message"]["parts"][0]["text"] == "test msg"

    async def test_send_task_includes_session_id_when_provided(self) -> None:
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.return_value = {
            "result": {"id": "t-1", "status": {"state": "submitted"}},
        }

        adapter = A2AAdapter(gateway_url="https://gw.example.com", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            await adapter.send_task(target_agent_url="http://target", message="hi", session_id="s-99")

        call_kwargs = mock_client.invoke_agent_runtime.call_args[1]
        payload = call_kwargs["payload"]
        assert payload["params"]["sessionId"] == "s-99"


# -- send_task 异常捕获 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestA2AAdapterSendTaskError:
    """send_task 异常捕获测试。"""

    async def test_send_task_exception_returns_failed(self) -> None:
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.side_effect = Exception("网络超时")

        adapter = A2AAdapter(gateway_url="https://gw.example.com", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.send_task(target_agent_url="http://agent", message="hello")
        assert result == A2ATaskResult(task_id="", status="failed")

    async def test_send_task_timeout_returns_failed(self) -> None:
        """模拟超时异常。"""
        mock_client = MagicMock()
        mock_client.invoke_agent_runtime.side_effect = TimeoutError("请求超时")

        adapter = A2AAdapter(gateway_url="https://gw.example.com", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.send_task(target_agent_url="http://agent", message="hello")
        assert result == A2ATaskResult(task_id="", status="failed")


# -- get_task_status 正常路径和错误处理 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestA2AAdapterGetTaskStatus:
    """get_task_status 测试。"""

    async def test_get_task_status_success(self) -> None:
        mock_client = MagicMock()
        mock_client.get_agent_runtime_task.return_value = {
            "result": {
                "status": {"state": "completed", "message": ""},
                "artifacts": [{"parts": [{"type": "text", "text": "结果文本"}]}],
            },
        }

        adapter = A2AAdapter(gateway_url="https://gw.example.com", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.get_task_status(task_id="task-abc")
        assert result.task_id == "task-abc"
        assert result.status == "completed"
        assert result.content == "结果文本"

    async def test_get_task_status_exception_returns_error(self) -> None:
        mock_client = MagicMock()
        mock_client.get_agent_runtime_task.side_effect = Exception("查询失败")

        adapter = A2AAdapter(gateway_url="https://gw.example.com", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.get_task_status(task_id="task-xyz")
        assert result == A2ATaskStatus(task_id="task-xyz", status="error", error="查询失败")
