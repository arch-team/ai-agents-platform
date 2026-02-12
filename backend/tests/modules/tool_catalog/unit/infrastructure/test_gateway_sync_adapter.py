"""GatewaySyncAdapter 单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.tool_catalog.infrastructure.external.gateway_sync_adapter import (
    GatewaySyncAdapter,
)


class TestGatewaySyncAdapterRegister:
    """register_tool 测试。"""

    @pytest.fixture
    def adapter(self):
        return GatewaySyncAdapter(
            gateway_id="gw-test-123",
            region="us-east-1",
        )

    @pytest.mark.asyncio
    async def test_register_tool_calls_create_gateway_target(self, adapter):
        mock_client = MagicMock()
        mock_client.create_gateway_target.return_value = {
            "gatewayTargetId": "target-abc-123",
        }

        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.register_tool(
                tool_id=1,
                tool_name="test-mcp-server",
                description="测试 MCP 工具",
                server_url="https://example.com/mcp",
                transport="sse",
            )

        assert result == "target-abc-123"
        mock_client.create_gateway_target.assert_called_once()
        call_kwargs = mock_client.create_gateway_target.call_args[1]
        assert call_kwargs["gatewayIdentifier"] == "gw-test-123"
        assert call_kwargs["name"] == "tool-1-test-mcp-server"

    @pytest.mark.asyncio
    async def test_register_tool_includes_mcp_target_config(self, adapter):
        mock_client = MagicMock()
        mock_client.create_gateway_target.return_value = {
            "gatewayTargetId": "target-xyz",
        }

        with patch.object(adapter, "_get_client", return_value=mock_client):
            await adapter.register_tool(
                tool_id=42,
                tool_name="my-tool",
                description="工具描述",
                server_url="https://my-mcp.example.com",
                transport="sse",
            )

        call_kwargs = mock_client.create_gateway_target.call_args[1]
        target_config = call_kwargs["targetConfiguration"]
        assert "mcpTarget" in target_config
        mcp_config = target_config["mcpTarget"]
        assert mcp_config["mcpServerUrl"] == "https://my-mcp.example.com"

    @pytest.mark.asyncio
    async def test_register_tool_raises_on_api_error(self, adapter):
        mock_client = MagicMock()
        mock_client.create_gateway_target.side_effect = Exception("API Error")

        with patch.object(adapter, "_get_client", return_value=mock_client), \
             pytest.raises(Exception, match="Gateway 工具注册失败"):
            await adapter.register_tool(
                tool_id=1,
                tool_name="broken-tool",
                description="",
                server_url="https://example.com",
                transport="sse",
            )


class TestGatewaySyncAdapterUnregister:
    """unregister_tool 测试。"""

    @pytest.fixture
    def adapter(self):
        return GatewaySyncAdapter(
            gateway_id="gw-test-123",
            region="us-east-1",
        )

    @pytest.mark.asyncio
    async def test_unregister_tool_calls_delete_gateway_target(self, adapter):
        mock_client = MagicMock()
        mock_client.delete_gateway_target.return_value = {}

        with patch.object(adapter, "_get_client", return_value=mock_client):
            await adapter.unregister_tool(
                tool_id=1,
                target_id="target-abc-123",
            )

        mock_client.delete_gateway_target.assert_called_once_with(
            gatewayIdentifier="gw-test-123",
            targetId="target-abc-123",
        )

    @pytest.mark.asyncio
    async def test_unregister_tool_raises_on_api_error(self, adapter):
        mock_client = MagicMock()
        mock_client.delete_gateway_target.side_effect = Exception("Not Found")

        with patch.object(adapter, "_get_client", return_value=mock_client), \
             pytest.raises(Exception, match="Gateway 工具注销失败"):
            await adapter.unregister_tool(
                tool_id=1,
                target_id="target-not-exist",
            )


class TestGatewaySyncAdapterNoOp:
    """未配置 Gateway ID 时降级为 NoOp。"""

    def test_empty_gateway_id_creates_adapter(self):
        adapter = GatewaySyncAdapter(gateway_id="", region="us-east-1")
        assert adapter._gateway_id == ""

    @pytest.mark.asyncio
    async def test_register_with_empty_gateway_id_returns_empty(self):
        adapter = GatewaySyncAdapter(gateway_id="", region="us-east-1")
        result = await adapter.register_tool(
            tool_id=1,
            tool_name="test",
            description="",
            server_url="https://example.com",
            transport="sse",
        )
        assert result == ""

    @pytest.mark.asyncio
    async def test_unregister_with_empty_gateway_id_is_noop(self):
        adapter = GatewaySyncAdapter(gateway_id="", region="us-east-1")
        # 不应抛出异常
        await adapter.unregister_tool(tool_id=1, target_id="any-id")
