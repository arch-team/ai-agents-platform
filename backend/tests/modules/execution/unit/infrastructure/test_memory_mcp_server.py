"""Memory MCP Server 配置工厂单元测试。"""

import pytest

from src.modules.execution.infrastructure.external.memory_mcp_server import (
    MemoryMcpConfig,
    build_memory_mcp_server_config,
)


@pytest.mark.unit
class TestBuildMemoryMcpServerConfig:
    """build_memory_mcp_server_config 返回格式测试。"""

    def test_returns_stdio_config_when_configured(self) -> None:
        config = MemoryMcpConfig(memory_id="mem-abc-123", region="us-east-1")
        result = build_memory_mcp_server_config(config)

        assert result["type"] == "stdio"
        assert result["command"] == "python"
        assert "-m" in result["args"]
        assert result["env"]["AGENTCORE_MEMORY_ID"] == "mem-abc-123"
        assert result["env"]["AWS_REGION"] == "us-east-1"

    def test_returns_empty_dict_when_no_memory_id(self) -> None:
        config = MemoryMcpConfig(memory_id="", region="us-east-1")
        result = build_memory_mcp_server_config(config)

        assert result == {}

    def test_config_includes_entrypoint_module(self) -> None:
        config = MemoryMcpConfig(memory_id="mem-xyz", region="us-west-2")
        result = build_memory_mcp_server_config(config)

        assert "memory_server_entrypoint" in result["args"][1]

    def test_returns_dict_type(self) -> None:
        config = MemoryMcpConfig(memory_id="mem-test", region="us-east-1")
        result = build_memory_mcp_server_config(config)

        assert isinstance(result, dict)
        assert "type" in result
        assert "command" in result
        assert "env" in result


@pytest.mark.unit
class TestMemoryMcpConfig:
    """MemoryMcpConfig 值对象测试。"""

    def test_is_frozen(self) -> None:
        config = MemoryMcpConfig(memory_id="mem-123", region="us-east-1")
        with pytest.raises(AttributeError):
            config.memory_id = "new-id"  # type: ignore[misc]

    def test_equality(self) -> None:
        config1 = MemoryMcpConfig(memory_id="mem-123", region="us-east-1")
        config2 = MemoryMcpConfig(memory_id="mem-123", region="us-east-1")
        assert config1 == config2
