"""AgentCore Gateway 工具同步接口。"""

from __future__ import annotations

from typing import Protocol


class IGatewaySyncService(Protocol):
    """AgentCore Gateway 工具注册/注销接口。

    工具审批通过后自动注册到 Gateway，废弃后自动移除。
    """

    async def register_tool(
        self,
        *,
        tool_id: int,
        tool_name: str,
        description: str,
        server_url: str,
        transport: str,
    ) -> str:
        """将 MCP Server 工具注册到 AgentCore Gateway。

        Returns:
            Gateway Target ID

        Raises:
            DomainError: Gateway API 调用失败
        """
        ...

    async def unregister_tool(self, *, tool_id: int, target_id: str) -> None:
        """从 AgentCore Gateway 移除工具。

        Raises:
            DomainError: Gateway API 调用失败
        """
        ...
