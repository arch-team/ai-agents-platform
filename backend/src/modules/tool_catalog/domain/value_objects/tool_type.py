"""Tool 类型枚举。"""

from enum import StrEnum


class ToolType(StrEnum):
    """Tool 接入类型。"""

    MCP_SERVER = "mcp_server"
    API = "api"
    FUNCTION = "function"
