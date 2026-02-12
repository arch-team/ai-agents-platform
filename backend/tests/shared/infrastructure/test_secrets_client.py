"""Secrets Manager 客户端测试。"""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.shared.infrastructure.secrets_client import (
    DatabaseCredentials,
    JwtCredentials,
    fetch_database_credentials,
    fetch_jwt_credentials,
    is_deployed_env,
)


class TestIsDeployedEnv:
    def test_development_is_not_deployed(self):
        assert is_deployed_env("development") is False

    def test_test_is_not_deployed(self):
        assert is_deployed_env("test") is False

    def test_dev_is_deployed(self):
        assert is_deployed_env("dev") is True

    def test_staging_is_deployed(self):
        assert is_deployed_env("staging") is True

    def test_production_is_deployed(self):
        assert is_deployed_env("production") is True


class TestFetchDatabaseCredentials:
    @patch("src.shared.infrastructure.secrets_client._get_secrets_client")
    def test_success(self, mock_get_client):
        secret_value = {
            "username": "admin",
            "password": "secret123",
            "dbname": "mydb",
            "host": "db.example.com",
            "port": "3306",
        }
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_value),
        }
        mock_get_client.return_value = mock_client

        result = fetch_database_credentials("arn:aws:secretsmanager:us-east-1:123:secret:test", "us-east-1")

        assert isinstance(result, DatabaseCredentials)
        assert result.username == "admin"
        assert result.password == "secret123"
        assert result.dbname == "mydb"
        assert result.host == "db.example.com"
        assert result.port == 3306

    @patch("src.shared.infrastructure.secrets_client._get_secrets_client")
    def test_missing_host_defaults_empty(self, mock_get_client):
        secret_value = {"username": "admin", "password": "pw", "dbname": "mydb"}
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {"SecretString": json.dumps(secret_value)}
        mock_get_client.return_value = mock_client

        result = fetch_database_credentials("arn:test", "us-east-1")
        assert result.host == ""
        assert result.port == 3306

    @patch("src.shared.infrastructure.secrets_client._get_secrets_client")
    def test_client_error_raises_runtime(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "not found"}},
            "GetSecretValue",
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="无法从 Secrets Manager 获取数据库凭证"):
            fetch_database_credentials("arn:bad", "us-east-1")

    @patch("src.shared.infrastructure.secrets_client._get_secrets_client")
    def test_invalid_json_raises_runtime(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {"SecretString": "not-json"}
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="数据库 Secret 格式不正确"):
            fetch_database_credentials("arn:bad", "us-east-1")

    @patch("src.shared.infrastructure.secrets_client._get_secrets_client")
    def test_missing_key_raises_runtime(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {"SecretString": json.dumps({"username": "admin"})}
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="数据库 Secret 格式不正确"):
            fetch_database_credentials("arn:bad", "us-east-1")


class TestFetchJwtCredentials:
    @patch("src.shared.infrastructure.secrets_client._get_secrets_client")
    def test_success(self, mock_get_client):
        secret_value = {"secret_key": "my-jwt-signing-key-that-is-very-long-and-secure"}
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {"SecretString": json.dumps(secret_value)}
        mock_get_client.return_value = mock_client

        result = fetch_jwt_credentials("arn:jwt", "us-east-1")

        assert isinstance(result, JwtCredentials)
        assert result.secret_key == "my-jwt-signing-key-that-is-very-long-and-secure"

    @patch("src.shared.infrastructure.secrets_client._get_secrets_client")
    def test_client_error_raises_runtime(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "access denied"}},
            "GetSecretValue",
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="无法从 Secrets Manager 获取 JWT 密钥"):
            fetch_jwt_credentials("arn:bad", "us-east-1")

    @patch("src.shared.infrastructure.secrets_client._get_secrets_client")
    def test_missing_key_raises_runtime(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {"SecretString": json.dumps({"wrong_key": "value"})}
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="JWT Secret 格式不正确"):
            fetch_jwt_credentials("arn:bad", "us-east-1")
