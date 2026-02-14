"""IdentityAdapter 单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.execution.infrastructure.external.identity_adapter import IdentityAdapter


# -- NoOp 降级测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestIdentityAdapterNoOp:
    """未配置 identity_pool_id 时的 NoOp 降级行为。"""

    async def test_exchange_token_returns_empty_string(self) -> None:
        adapter = IdentityAdapter(identity_pool_id="", region="us-east-1")
        result = await adapter.exchange_token(platform_jwt="eyJ...")
        assert result == ""

    async def test_validate_gateway_token_returns_empty_dict(self) -> None:
        adapter = IdentityAdapter(identity_pool_id="", region="us-east-1")
        result = await adapter.validate_gateway_token(token="tok-123")
        assert result == {}

    async def test_register_oauth_client_returns_empty_dict(self) -> None:
        adapter = IdentityAdapter(identity_pool_id="", region="us-east-1")
        result = await adapter.register_oauth_client(
            client_name="test-app",
            redirect_uris=["https://example.com/callback"],
        )
        assert result == {}


# -- exchange_token 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestIdentityAdapterExchangeToken:
    """exchange_token 正常路径测试。"""

    @patch("src.modules.execution.infrastructure.external.identity_adapter.boto3")
    async def test_exchange_token_success(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_token.return_value = {"accessToken": "ac-token-xyz"}
        mock_boto3.client.return_value = mock_client

        adapter = IdentityAdapter(identity_pool_id="pool-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.exchange_token(platform_jwt="eyJ.platform.jwt")
        assert result == "ac-token-xyz"
        mock_client.get_token.assert_called_once_with(
            identityPoolId="pool-abc",
            token="eyJ.platform.jwt",
        )

    @patch("src.modules.execution.infrastructure.external.identity_adapter.boto3")
    async def test_exchange_token_client_error_returns_empty(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_token.side_effect = Exception("API 调用失败")
        mock_boto3.client.return_value = mock_client

        adapter = IdentityAdapter(identity_pool_id="pool-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.exchange_token(platform_jwt="eyJ.invalid")
        assert result == ""


# -- validate_gateway_token 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestIdentityAdapterValidateGatewayToken:
    """validate_gateway_token 正常路径测试。"""

    @patch("src.modules.execution.infrastructure.external.identity_adapter.boto3")
    async def test_validate_gateway_token_success(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.validate_token.return_value = {
            "claims": {"sub": "user-123", "scope": "agent:execute"},
        }
        mock_boto3.client.return_value = mock_client

        adapter = IdentityAdapter(identity_pool_id="pool-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.validate_gateway_token(token="ac-token-xyz")
        assert result == {"sub": "user-123", "scope": "agent:execute"}
        mock_client.validate_token.assert_called_once_with(
            identityPoolId="pool-abc",
            token="ac-token-xyz",
        )

    @patch("src.modules.execution.infrastructure.external.identity_adapter.boto3")
    async def test_validate_gateway_token_client_error_returns_empty_dict(
        self,
        mock_boto3: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.validate_token.side_effect = Exception("验证失败")
        mock_boto3.client.return_value = mock_client

        adapter = IdentityAdapter(identity_pool_id="pool-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.validate_gateway_token(token="invalid-token")
        assert result == {}


# -- register_oauth_client 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestIdentityAdapterRegisterOAuthClient:
    """register_oauth_client 正常路径测试。"""

    @patch("src.modules.execution.infrastructure.external.identity_adapter.boto3")
    async def test_register_oauth_client_success(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.create_oauth_client.return_value = {
            "clientId": "client-abc",
            "clientSecret": "secret-xyz",
        }
        mock_boto3.client.return_value = mock_client

        adapter = IdentityAdapter(identity_pool_id="pool-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.register_oauth_client(
            client_name="my-app",
            redirect_uris=["https://app.example.com/callback"],
        )
        assert result == {"clientId": "client-abc", "clientSecret": "secret-xyz"}
        mock_client.create_oauth_client.assert_called_once_with(
            identityPoolId="pool-abc",
            clientName="my-app",
            redirectUris=["https://app.example.com/callback"],
        )

    @patch("src.modules.execution.infrastructure.external.identity_adapter.boto3")
    async def test_register_oauth_client_error_returns_empty_dict(
        self,
        mock_boto3: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_oauth_client.side_effect = Exception("注册失败")
        mock_boto3.client.return_value = mock_client

        adapter = IdentityAdapter(identity_pool_id="pool-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.register_oauth_client(
            client_name="my-app",
            redirect_uris=["https://app.example.com/callback"],
        )
        assert result == {}
