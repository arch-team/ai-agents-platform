"""AWS Secrets Manager 客户端 — 部署环境下从 Secrets Manager 读取凭证。

本地开发环境 (APP_ENV=development/test) 不使用此模块，直接通过 .env 文件加载。
部署环境 (APP_ENV=dev/staging/production) 应用启动时从 Secrets Manager 获取 DB 凭证和 JWT 密钥。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)

# 本地环境标识 — 这些环境不从 Secrets Manager 读取
_LOCAL_ENVS = frozenset({"development", "test"})


@dataclass(frozen=True)
class DatabaseCredentials:
    """从 Secrets Manager 解析的数据库凭证。"""

    username: str
    password: str
    dbname: str
    host: str
    port: int


@dataclass(frozen=True)
class JwtCredentials:
    """从 Secrets Manager 解析的 JWT 签名密钥。"""

    secret_key: str


def is_deployed_env(app_env: str) -> bool:
    """判断是否为部署环境 (需从 Secrets Manager 读取凭证)。"""
    return app_env not in _LOCAL_ENVS


def _get_secrets_client(region: str) -> Any:  # noqa: ANN401
    """创建 Secrets Manager 客户端 (ECS Task Role 自动提供凭证)。"""
    return boto3.client("secretsmanager", region_name=region)


def _fetch_secret(secret_arn: str, region: str, *, client_label: str, format_label: str) -> dict[str, Any]:
    """从 Secrets Manager 获取并解析 JSON Secret。

    Raises:
        RuntimeError: Secret 不存在或格式不正确时抛出。
    """
    try:
        client = _get_secrets_client(region)
        response = client.get_secret_value(SecretId=secret_arn)
        return dict(json.loads(response["SecretString"]))
    except ClientError as e:
        msg = f"无法从 Secrets Manager 获取{client_label}: {e}"
        raise RuntimeError(msg) from e
    except (KeyError, json.JSONDecodeError) as e:
        msg = f"{format_label} Secret 格式不正确: {e}"
        raise RuntimeError(msg) from e


def fetch_database_credentials(secret_arn: str, region: str) -> DatabaseCredentials:
    """从 Secrets Manager 获取数据库凭证。

    Raises:
        RuntimeError: Secret 不存在或格式不正确时抛出。
    """
    try:
        secret_dict = _fetch_secret(
            secret_arn,
            region,
            client_label="数据库凭证",
            format_label="数据库",
        )
        return DatabaseCredentials(
            username=secret_dict["username"],
            password=secret_dict["password"],
            dbname=secret_dict["dbname"],
            host=secret_dict.get("host", ""),
            port=int(secret_dict.get("port", 3306)),
        )
    except KeyError as e:
        msg = f"数据库 Secret 格式不正确: {e}"
        raise RuntimeError(msg) from e


def fetch_jwt_credentials(secret_arn: str, region: str) -> JwtCredentials:
    """从 Secrets Manager 获取 JWT 签名密钥。

    Raises:
        RuntimeError: Secret 不存在或格式不正确时抛出。
    """
    try:
        secret_dict = _fetch_secret(
            secret_arn,
            region,
            client_label=" JWT 密钥",
            format_label="JWT",
        )
        return JwtCredentials(secret_key=secret_dict["secret_key"])
    except KeyError as e:
        msg = f"JWT Secret 格式不正确: {e}"
        raise RuntimeError(msg) from e
