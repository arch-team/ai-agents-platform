"""Tool 配置值对象（frozen dataclass，不可变）。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolConfig:
    """Tool 连接配置，不可变值对象。"""

    # MCP Server 配置
    server_url: str = ""
    transport: str = "stdio"  # stdio | sse | streamable-http

    # API 配置
    endpoint_url: str = ""
    method: str = "POST"
    headers: tuple[tuple[str, str], ...] = ()

    # Function 配置
    runtime: str = ""
    handler: str = ""
    code_uri: str = ""

    # 通用认证配置
    auth_type: str = "none"  # none | api_key | oauth
    auth_config: tuple[tuple[str, str], ...] = ()
