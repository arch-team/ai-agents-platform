"""AgentCore Identity 适配器。

SDK-First: 薄封装层，通过 boto3 调用 AgentCore Identity API。
未配置 identity_pool_id 时降级为 NoOp。
"""

import asyncio
from functools import lru_cache
from typing import Any

import boto3
import structlog


logger = structlog.get_logger(__name__)


class IdentityAdapter:
    """AgentCore Identity OAuth 2.0 适配器。"""

    def __init__(self, *, identity_pool_id: str, region: str) -> None:
        self._identity_pool_id = identity_pool_id
        self._region = region

    @lru_cache(maxsize=1)
    def _get_client(self) -> Any:
        """获取 bedrock-agentcore 客户端 (懒加载单例)。"""
        return boto3.client("bedrock-agentcore", region_name=self._region)

    async def exchange_token(self, platform_jwt: str) -> str:
        """将平台 JWT 交换为 AgentCore 访问令牌。

        未配置 identity_pool_id 时返回空字符串。
        """
        if not self._identity_pool_id:
            logger.debug("identity_exchange_skip", reason="identity_pool_id 未配置")
            return ""

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.get_token,
                identityPoolId=self._identity_pool_id,
                token=platform_jwt,
            )
        except Exception:
            logger.exception("identity_exchange_failed")
            return ""

        access_token: str = response.get("accessToken", "")
        logger.info("identity_token_exchanged")
        return access_token

    async def validate_gateway_token(self, token: str) -> dict[str, str]:
        """验证 Gateway 入站令牌，返回身份声明。

        未配置时降级返回空 dict。
        """
        if not self._identity_pool_id:
            logger.debug("identity_validate_skip", reason="identity_pool_id 未配置")
            return {}

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.validate_token,
                identityPoolId=self._identity_pool_id,
                token=token,
            )
        except Exception:
            logger.exception("identity_validate_failed")
            return {}

        claims: dict[str, str] = response.get("claims", {})
        logger.info("identity_token_validated", sub=claims.get("sub", ""))
        return claims

    async def register_oauth_client(self, client_name: str, redirect_uris: list[str]) -> dict[str, str]:
        """注册 OAuth 2.0 客户端应用。

        返回 client_id 和 client_secret。未配置时降级返回空 dict。
        """
        if not self._identity_pool_id:
            logger.debug("identity_register_skip", reason="identity_pool_id 未配置")
            return {}

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.create_oauth_client,
                identityPoolId=self._identity_pool_id,
                clientName=client_name,
                redirectUris=redirect_uris,
            )
        except Exception:
            logger.exception("identity_register_failed", client_name=client_name)
            return {}

        result: dict[str, str] = {
            "clientId": response.get("clientId", ""),
            "clientSecret": response.get("clientSecret", ""),
        }
        logger.info("identity_client_registered", client_name=client_name)
        return result
