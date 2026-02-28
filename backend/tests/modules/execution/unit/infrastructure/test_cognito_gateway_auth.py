"""CognitoGatewayAuthService 单元测试。"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.modules.execution.infrastructure.external.cognito_gateway_auth import (
    _EXPIRY_BUFFER_SECONDS,
    CognitoGatewayAuthService,
)


def _make_service(
    *,
    token_endpoint: str = "https://cognito.example.com/oauth2/token",
    client_id: str = "test-client-id",
    client_secret: str = "test-client-secret",
    scopes: str = "gateway/invoke",
) -> CognitoGatewayAuthService:
    return CognitoGatewayAuthService(
        token_endpoint=token_endpoint,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )


def _make_token_response(
    *,
    access_token: str = "test-access-token",
    expires_in: int = 3600,
) -> httpx.Response:
    """创建模拟的 Cognito Token 响应。"""
    return httpx.Response(
        status_code=200,
        json={
            "access_token": access_token,
            "expires_in": expires_in,
            "token_type": "Bearer",
        },
        request=httpx.Request("POST", "https://cognito.example.com/oauth2/token"),
    )


@pytest.mark.unit
class TestCognitoGatewayAuth:
    @pytest.mark.asyncio
    async def test_first_request_fetches_token(self) -> None:
        """首次调用应发起 HTTP 请求获取 Token。"""
        service = _make_service()
        mock_response = _make_token_response(access_token="my-token")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
            token = await service.get_bearer_token()

        assert token == "my-token"
        mock_post.assert_called_once()
        # 验证请求参数
        call_kwargs = mock_post.call_args
        assert call_kwargs.args[0] == "https://cognito.example.com/oauth2/token"
        assert call_kwargs.kwargs["data"]["grant_type"] == "client_credentials"
        assert call_kwargs.kwargs["data"]["client_id"] == "test-client-id"
        assert call_kwargs.kwargs["data"]["client_secret"] == "test-client-secret"
        assert call_kwargs.kwargs["data"]["scope"] == "gateway/invoke"

    @pytest.mark.asyncio
    async def test_cached_token_no_second_request(self) -> None:
        """缓存有效期内第二次调用不发起 HTTP 请求。"""
        service = _make_service()
        mock_response = _make_token_response(access_token="cached-token", expires_in=3600)

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
            token1 = await service.get_bearer_token()
            token2 = await service.get_bearer_token()

        assert token1 == "cached-token"
        assert token2 == "cached-token"
        # 只发起一次 HTTP 请求
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_expired_token_triggers_refresh(self) -> None:
        """Token 过期后应重新请求。"""
        service = _make_service()
        response1 = _make_token_response(access_token="old-token", expires_in=3600)
        response2 = _make_token_response(access_token="new-token", expires_in=3600)

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=[response1, response2]) as mock_post:
            token1 = await service.get_bearer_token()
            assert token1 == "old-token"

            # 模拟 Token 已过期: 直接修改过期时间
            service._token_expires_at = time.monotonic() - 1

            token2 = await service.get_bearer_token()
            assert token2 == "new-token"

        assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_requests_single_refresh(self) -> None:
        """并发请求只触发一次 Token 刷新。"""
        service = _make_service()

        call_count = 0

        async def _slow_post(*args: object, **kwargs: object) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)  # 模拟网络延迟
            return _make_token_response(access_token="concurrent-token")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=_slow_post):
            results = await asyncio.gather(
                service.get_bearer_token(),
                service.get_bearer_token(),
                service.get_bearer_token(),
            )

        # 所有并发请求获得相同 Token
        assert all(r == "concurrent-token" for r in results)
        # 只发起一次 HTTP 请求（Lock 保护）
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_request_failure_returns_empty_string(self) -> None:
        """HTTP 请求失败时返回空字符串。"""
        service = _make_service()

        with patch(
            "httpx.AsyncClient.post",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=MagicMock(status_code=401),
            ),
        ):
            token = await service.get_bearer_token()

        assert token == ""

    @pytest.mark.asyncio
    async def test_failure_clears_cache(self) -> None:
        """请求失败后清除缓存，下次重新请求。"""
        service = _make_service()
        success_response = _make_token_response(access_token="recovered-token")

        with patch(
            "httpx.AsyncClient.post",
            new_callable=AsyncMock,
            side_effect=[
                httpx.ConnectError("连接失败"),
                success_response,
            ],
        ) as mock_post:
            # 第一次失败
            token1 = await service.get_bearer_token()
            assert token1 == ""

            # 第二次恢复
            token2 = await service.get_bearer_token()
            assert token2 == "recovered-token"

        assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_token_refreshed_before_expiry_buffer(self) -> None:
        """Token 在过期前 _EXPIRY_BUFFER_SECONDS 秒刷新。"""
        service = _make_service()
        # expires_in 只比 buffer 多 1 秒
        short_response = _make_token_response(access_token="short-lived", expires_in=_EXPIRY_BUFFER_SECONDS + 1)
        refresh_response = _make_token_response(access_token="refreshed")

        with patch(
            "httpx.AsyncClient.post",
            new_callable=AsyncMock,
            side_effect=[short_response, refresh_response],
        ) as mock_post:
            token1 = await service.get_bearer_token()
            assert token1 == "short-lived"

            # 模拟时间流逝: Token 即将过期 (在 buffer 内)
            service._token_expires_at = time.monotonic() - 0.1

            token2 = await service.get_bearer_token()
            assert token2 == "refreshed"

        assert mock_post.call_count == 2
