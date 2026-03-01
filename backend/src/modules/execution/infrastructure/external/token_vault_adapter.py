"""AgentCore Identity Token Vault 适配器。

SDK-First: 薄封装层，通过 boto3 调用 AgentCore Identity Token Vault API。
管理第三方 API Key 的安全存储和检索，供 Agent 执行时使用。

未配置 identity_pool_id 时降级为 NoOp。
"""

import asyncio
from functools import lru_cache
from typing import Any

import structlog


logger = structlog.get_logger(__name__)


class TokenVaultAdapter:
    """AgentCore Token Vault — 第三方 API Key 安全管理。"""

    def __init__(self, *, identity_pool_id: str, region: str) -> None:
        self._identity_pool_id = identity_pool_id
        self._region = region

    @lru_cache(maxsize=1)
    def _get_client(self) -> Any:
        """获取 bedrock-agentcore 客户端 (懒加载单例)。"""
        import boto3

        return boto3.client("bedrock-agentcore", region_name=self._region)

    async def store_api_key(
        self,
        *,
        key_name: str,
        api_key: str,
        description: str = "",
    ) -> str:
        """将第三方 API Key 存储到 Token Vault。

        返回 credential_id。未配置时返回空字符串。
        """
        if not self._identity_pool_id:
            logger.debug("token_vault_store_skip", reason="identity_pool_id 未配置")
            return ""

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.create_credential,
                identityPoolId=self._identity_pool_id,
                credentialName=key_name,
                credentialValue=api_key,
                description=description,
                credentialType="API_KEY",
            )
        except Exception:
            logger.exception("token_vault_store_failed", key_name=key_name)
            return ""

        credential_id: str = response.get("credentialId", "")
        logger.info("token_vault_stored", key_name=key_name, credential_id=credential_id)
        return credential_id

    async def retrieve_api_key(self, credential_id: str) -> str:
        """从 Token Vault 检索 API Key。

        返回 API Key 明文。未配置或不存在时返回空字符串。
        """
        if not self._identity_pool_id:
            logger.debug("token_vault_retrieve_skip", reason="identity_pool_id 未配置")
            return ""

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.get_credential,
                identityPoolId=self._identity_pool_id,
                credentialId=credential_id,
            )
        except Exception:
            logger.exception("token_vault_retrieve_failed", credential_id=credential_id)
            return ""

        return str(response.get("credentialValue", ""))

    async def delete_api_key(self, credential_id: str) -> bool:
        """从 Token Vault 删除 API Key。

        返回是否删除成功。未配置时返回 False。
        """
        if not self._identity_pool_id:
            return False

        try:
            client = self._get_client()
            await asyncio.to_thread(
                client.delete_credential,
                identityPoolId=self._identity_pool_id,
                credentialId=credential_id,
            )
        except Exception:
            logger.exception("token_vault_delete_failed", credential_id=credential_id)
            return False

        logger.info("token_vault_deleted", credential_id=credential_id)
        return True

    async def list_api_keys(self) -> list[dict[str, str]]:
        """列出 Token Vault 中所有 API Key 的元数据 (不含明文)。

        返回 [{credential_id, key_name, description}]。
        """
        if not self._identity_pool_id:
            return []

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.list_credentials,
                identityPoolId=self._identity_pool_id,
                credentialType="API_KEY",
            )
        except Exception:
            logger.exception("token_vault_list_failed")
            return []

        return [
            {
                "credential_id": cred.get("credentialId", ""),
                "key_name": cred.get("credentialName", ""),
                "description": cred.get("description", ""),
            }
            for cred in response.get("credentials", [])
        ]
