"""Memory MCP Server 配置模块单元测试。"""

from src.modules.execution.infrastructure.external.memory_mcp_server import (
    MemoryMcpConfig,
    build_memory_mcp_server_config,
)


class TestMemoryMcpConfig:
    """MemoryMcpConfig 数据类测试。"""

    def test_creates_config_with_required_fields(self) -> None:
        config = MemoryMcpConfig(memory_id="mem-abc-123", region="us-east-1")
        assert config.memory_id == "mem-abc-123"
        assert config.region == "us-east-1"

    def test_empty_memory_id(self) -> None:
        config = MemoryMcpConfig(memory_id="", region="us-east-1")
        assert config.memory_id == ""


class TestBuildMemoryMcpServerConfig:
    """build_memory_mcp_server_config 测试。"""

    def test_returns_stdio_mcp_config(self) -> None:
        config = MemoryMcpConfig(memory_id="mem-123", region="us-east-1")
        result = build_memory_mcp_server_config(config)

        assert result["type"] == "stdio"
        assert "command" in result
        assert result["env"]["AGENTCORE_MEMORY_ID"] == "mem-123"
        assert result["env"]["AWS_REGION"] == "us-east-1"

    def test_returns_empty_dict_when_no_memory_id(self) -> None:
        config = MemoryMcpConfig(memory_id="", region="us-east-1")
        result = build_memory_mcp_server_config(config)
        assert result == {}

    def test_command_points_to_memory_server(self) -> None:
        config = MemoryMcpConfig(memory_id="mem-456", region="ap-northeast-1")
        result = build_memory_mcp_server_config(config)

        assert "memory" in result["command"].lower() or "memory" in str(result.get("args", []))
