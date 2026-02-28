"""Cognito Client Credentials Grant 实现 Gateway 认证。

通过 Cognito /oauth2/token 端点获取 access_token,
支持 Token 缓存和并发安全刷新。
"""

import asyncio
import time

import httpx
import structlog

from src.modules.execution.application.interfaces.gateway_auth import IGatewayAuthService


logger = structlog.get_logger(__name__)

# Token 过期前提前刷新的秒数
_EXPIRY_BUFFER_SECONDS = 60


class CognitoGatewayAuthService(IGatewayAuthService):
    """通过 Cognito Client Credentials Grant 获取 Gateway Bearer Token。"""

    def __init__(
        self,
        *,
        token_endpoint: str,
        client_id: str,
        client_secret: str,
        scopes: str,
    ) -> None:
        self._token_endpoint = token_endpoint
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = scopes
        self._cached_token: str = ""
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_bearer_token(self) -> str:
        """获取 Gateway Bearer Token, 优先使用缓存。

        获取失败时返回空字符串 (触发降级逻辑)。
        """
        if self._cached_token and time.monotonic() < self._token_expires_at:
            return self._cached_token

        async with self._lock:
            # Double-check: 其他协程可能已刷新
            if self._cached_token and time.monotonic() < self._token_expires_at:
                return self._cached_token

            return await self._refresh_token()

    async def _refresh_token(self) -> str:
        """向 Cognito 请求新 Token。失败返回空字符串。"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self._token_endpoint,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "scope": self._scopes,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()

            body = response.json()
            access_token: str = body["access_token"]
            expires_in: int = body.get("expires_in", 3600)

            self._cached_token = access_token
            self._token_expires_at = time.monotonic() + expires_in - _EXPIRY_BUFFER_SECONDS

            logger.info("gateway_token_refreshed", expires_in=expires_in)
        except Exception:
            logger.exception("gateway_token_refresh_failed")
            self._cached_token = ""
            self._token_expires_at = 0.0
            return ""
        else:
            return access_token
