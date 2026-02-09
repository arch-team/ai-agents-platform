"""ToolType 枚举单元测试。"""

import pytest

from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType


@pytest.mark.unit
class TestToolType:
    def test_mcp_server_value(self) -> None:
        assert ToolType.MCP_SERVER == "mcp_server"

    def test_api_value(self) -> None:
        assert ToolType.API == "api"

    def test_function_value(self) -> None:
        assert ToolType.FUNCTION == "function"

    def test_is_str_enum(self) -> None:
        assert isinstance(ToolType.MCP_SERVER, str)

    def test_all_members(self) -> None:
        members = {t.value for t in ToolType}
        assert members == {"mcp_server", "api", "function"}
