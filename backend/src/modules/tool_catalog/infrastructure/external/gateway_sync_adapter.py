"""AgentCore Gateway 工具同步适配器。

将 MCP_SERVER 类型的已审批工具注册到 AgentCore Gateway，
使 Claude Agent SDK 可通过 Gateway MCP 端点调用工具。

未配置 Gateway ID 时降级为 NoOp (开发环境)。
"""

import asyncio
from functools import lru_cache
from typing import Protocol, cast

import structlog

from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


class _AgentCoreGatewayClient(Protocol):
    """AgentCore Gateway boto3 客户端的类型协议。"""

    def create_gateway_target(self, **kwargs: object) -> dict[str, str]: ...
    def delete_gateway_target(self, **kwargs: object) -> dict[str, str]: ...


class GatewaySyncAdapter:
    """AgentCore Gateway 工具注册/注销适配器。"""

    def __init__(self, *, gateway_id: str, region: str) -> None:
        self._gateway_id = gateway_id
        self._region = region

    @lru_cache(maxsize=1)
    def _get_client(self) -> _AgentCoreGatewayClient:
        """获取 bedrock-agentcore 控制面客户端 (懒加载单例)。"""
        import boto3

        return cast(
            "_AgentCoreGatewayClient",
            boto3.client("bedrock-agentcore", region_name=self._region),
        )

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
            Gateway Target ID (空字符串表示未配置 Gateway)

        Raises:
            DomainError: Gateway API 调用失败
        """
        if not self._gateway_id:
            logger.warning("gateway_sync_skip_register", tool_id=tool_id, reason="gateway_id 未配置")
            return ""

        target_name = f"tool-{tool_id}-{tool_name}"

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.create_gateway_target,
                gatewayIdentifier=self._gateway_id,
                name=target_name,
                description=f"{description} [transport={transport}]",
                targetConfiguration={
                    "mcpTarget": {
                        "mcpServerUrl": server_url,
                        "openApiSchema": {},
                    },
                },
            )
        except Exception as e:
            logger.exception("gateway_tool_register_failed", tool_id=tool_id)
            raise DomainError(
                message=f"Gateway 工具注册失败: {tool_name}",
                code="GATEWAY_REGISTER_ERROR",
            ) from e

        target_id: str = response["gatewayTargetId"]
        logger.info(
            "gateway_tool_registered",
            tool_id=tool_id,
            tool_name=tool_name,
            target_id=target_id,
        )
        return target_id

    async def unregister_tool(self, *, tool_id: int, target_id: str) -> None:
        """从 AgentCore Gateway 移除工具。

        Raises:
            DomainError: Gateway API 调用失败
        """
        if not self._gateway_id:
            logger.warning("gateway_sync_skip_unregister", tool_id=tool_id, reason="gateway_id 未配置")
            return

        try:
            client = self._get_client()
            await asyncio.to_thread(
                client.delete_gateway_target,
                gatewayIdentifier=self._gateway_id,
                targetId=target_id,
            )
            logger.info(
                "gateway_tool_unregistered",
                tool_id=tool_id,
                target_id=target_id,
            )
        except Exception as e:
            logger.exception("gateway_tool_unregister_failed", tool_id=tool_id, target_id=target_id)
            raise DomainError(
                message=f"Gateway 工具注销失败: tool_id={tool_id}",
                code="GATEWAY_UNREGISTER_ERROR",
            ) from e
