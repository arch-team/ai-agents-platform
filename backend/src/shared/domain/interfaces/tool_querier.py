"""跨模块工具查询接口。

execution 模块依赖此接口获取 Agent 可用工具列表，
避免直接导入 tool_catalog 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovedToolInfo:
    """已审批工具的最小信息集。"""

    id: int
    name: str
    description: str
    tool_type: str  # "mcp_server" | "api" | "function"
    # MCP Server 配置
    server_url: str = ""
    transport: str = "stdio"  # stdio | sse | streamable-http
    # API 配置
    endpoint_url: str = ""
    method: str = ""
    # Function 配置
    runtime: str = ""
    handler: str = ""
    # 认证
    auth_type: str = "none"


class IToolQuerier(ABC):
    """跨模块工具查询接口。"""

    @abstractmethod
    async def list_approved_tools(self) -> list[ApprovedToolInfo]: ...  # noqa: D102
