"""TokenVaultAdapter 单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.execution.infrastructure.external.token_vault_adapter import TokenVaultAdapter


# -- NoOp 降级测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestTokenVaultAdapterNoOp:
    """未配置 identity_pool_id 时的 NoOp 降级行为。"""

    async def test_store_api_key_returns_empty(self) -> None:
        adapter = TokenVaultAdapter(identity_pool_id="", region="us-east-1")
        result = await adapter.store_api_key(key_name="openai", api_key="sk-xxx")
        assert result == ""

    async def test_retrieve_api_key_returns_empty(self) -> None:
        adapter = TokenVaultAdapter(identity_pool_id="", region="us-east-1")
        result = await adapter.retrieve_api_key(credential_id="cred-123")
        assert result == ""

    async def test_delete_api_key_returns_false(self) -> None:
        adapter = TokenVaultAdapter(identity_pool_id="", region="us-east-1")
        result = await adapter.delete_api_key(credential_id="cred-123")
        assert result is False

    async def test_list_api_keys_returns_empty_list(self) -> None:
        adapter = TokenVaultAdapter(identity_pool_id="", region="us-east-1")
        result = await adapter.list_api_keys()
        assert result == []


# -- store_api_key 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestTokenVaultAdapterStoreApiKey:
    """store_api_key 测试。"""

    async def test_store_api_key_success(self) -> None:
        mock_client = MagicMock()
        mock_client.create_credential.return_value = {"credentialId": "cred-abc-123"}

        adapter = TokenVaultAdapter(identity_pool_id="pool-xyz", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.store_api_key(
                key_name="openai-key",
                api_key="sk-test-key-value",
                description="OpenAI API Key",
            )
        assert result == "cred-abc-123"
        mock_client.create_credential.assert_called_once_with(
            identityPoolId="pool-xyz",
            credentialName="openai-key",
            credentialValue="sk-test-key-value",
            description="OpenAI API Key",
            credentialType="API_KEY",
        )

    async def test_store_api_key_exception_returns_empty(self) -> None:
        mock_client = MagicMock()
        mock_client.create_credential.side_effect = Exception("存储失败")

        adapter = TokenVaultAdapter(identity_pool_id="pool-xyz", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.store_api_key(key_name="key", api_key="sk-xxx")
        assert result == ""


# -- retrieve_api_key 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestTokenVaultAdapterRetrieveApiKey:
    """retrieve_api_key 测试。"""

    async def test_retrieve_api_key_success(self) -> None:
        mock_client = MagicMock()
        mock_client.get_credential.return_value = {"credentialValue": "sk-real-secret-key"}

        adapter = TokenVaultAdapter(identity_pool_id="pool-xyz", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.retrieve_api_key(credential_id="cred-abc")
        assert result == "sk-real-secret-key"

    async def test_retrieve_nonexistent_key_returns_empty(self) -> None:
        """模拟不存在的 Key —— SDK 抛出异常。"""
        mock_client = MagicMock()
        mock_client.get_credential.side_effect = Exception("ResourceNotFoundException")

        adapter = TokenVaultAdapter(identity_pool_id="pool-xyz", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.retrieve_api_key(credential_id="cred-not-exist")
        assert result == ""

    async def test_retrieve_api_key_exception_returns_empty(self) -> None:
        mock_client = MagicMock()
        mock_client.get_credential.side_effect = Exception("网络错误")

        adapter = TokenVaultAdapter(identity_pool_id="pool-xyz", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.retrieve_api_key(credential_id="cred-abc")
        assert result == ""


# -- delete_api_key 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestTokenVaultAdapterDeleteApiKey:
    """delete_api_key 测试。"""

    async def test_delete_api_key_success(self) -> None:
        mock_client = MagicMock()
        mock_client.delete_credential.return_value = None

        adapter = TokenVaultAdapter(identity_pool_id="pool-xyz", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.delete_api_key(credential_id="cred-abc")
        assert result is True

    async def test_delete_api_key_exception_returns_false(self) -> None:
        mock_client = MagicMock()
        mock_client.delete_credential.side_effect = Exception("删除失败")

        adapter = TokenVaultAdapter(identity_pool_id="pool-xyz", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.delete_api_key(credential_id="cred-abc")
        assert result is False


# -- list_api_keys 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestTokenVaultAdapterListApiKeys:
    """list_api_keys 测试。"""

    async def test_list_api_keys_success(self) -> None:
        mock_client = MagicMock()
        mock_client.list_credentials.return_value = {
            "credentials": [
                {"credentialId": "cred-1", "credentialName": "openai", "description": "OpenAI Key"},
                {"credentialId": "cred-2", "credentialName": "anthropic", "description": "Anthropic Key"},
            ],
        }

        adapter = TokenVaultAdapter(identity_pool_id="pool-xyz", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.list_api_keys()
        assert len(result) == 2
        assert result[0] == {"credential_id": "cred-1", "key_name": "openai", "description": "OpenAI Key"}
        assert result[1] == {"credential_id": "cred-2", "key_name": "anthropic", "description": "Anthropic Key"}

    async def test_list_api_keys_exception_returns_empty_list(self) -> None:
        mock_client = MagicMock()
        mock_client.list_credentials.side_effect = Exception("列表查询失败")

        adapter = TokenVaultAdapter(identity_pool_id="pool-xyz", region="us-east-1")
        adapter._get_client.cache_clear()
        with patch.object(adapter, "_get_client", return_value=mock_client):
            result = await adapter.list_api_keys()
        assert result == []
