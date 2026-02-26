"""Settings 配置管理测试。"""

from unittest.mock import patch

import pytest
from pydantic import SecretStr

from src.shared.infrastructure.secrets_client import DatabaseCredentials, JwtCredentials
from src.shared.infrastructure.settings import Settings, get_settings


@pytest.mark.unit
class TestSettings:
    """Settings 默认值测试。

    使用 _env_file=None 隔离 .env 文件，确保测试验证的是代码中定义的默认值，
    而非被 .env 覆盖后的值。
    """

    def test_default_app_name(self):
        settings = Settings(_env_file=None)
        assert settings.APP_NAME == "ai-agents-platform"

    def test_default_app_env(self, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)
        settings = Settings(_env_file=None)
        assert settings.APP_ENV == "development"

    def test_default_debug_false(self):
        settings = Settings(_env_file=None)
        assert settings.APP_DEBUG is False

    def test_database_defaults(self):
        settings = Settings(_env_file=None)
        assert settings.DATABASE_HOST == "localhost"
        assert settings.DATABASE_PORT == 3306
        assert settings.DATABASE_NAME == "ai_agents_platform"
        assert settings.DATABASE_USER == "root"

    def test_database_password_is_secret(self):
        settings = Settings(DATABASE_PASSWORD=SecretStr("my-secret-pw"), _env_file=None)
        assert isinstance(settings.DATABASE_PASSWORD, SecretStr)
        assert settings.DATABASE_PASSWORD.get_secret_value() == "my-secret-pw"

    def test_database_password_default(self):
        settings = Settings(_env_file=None)
        assert settings.DATABASE_PASSWORD.get_secret_value() == "changeme"

    def test_jwt_defaults(self):
        settings = Settings(_env_file=None)
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_jwt_secret_key_is_secret(self):
        settings = Settings(JWT_SECRET_KEY=SecretStr("my-jwt-secret"), _env_file=None)
        assert isinstance(settings.JWT_SECRET_KEY, SecretStr)
        assert settings.JWT_SECRET_KEY.get_secret_value() == "my-jwt-secret"

    def test_aws_region_configurable(self):
        settings = Settings(AWS_REGION="ap-northeast-1", _env_file=None)
        assert settings.AWS_REGION == "ap-northeast-1"

    def test_log_level_default(self):
        settings = Settings(_env_file=None)
        assert settings.LOG_LEVEL == "INFO"

    def test_database_url_property(self):
        settings = Settings(
            DATABASE_HOST="db-host",
            DATABASE_PORT=3307,
            DATABASE_NAME="testdb",
            DATABASE_USER="testuser",
            DATABASE_PASSWORD=SecretStr("testpw"),
            _env_file=None,
        )
        url = settings.database_url
        assert "asyncmy" in url
        assert "testuser" in url
        assert "testpw" in url
        assert "db-host" in url
        assert "3307" in url
        assert "testdb" in url


@pytest.mark.unit
class TestSettingsValidation:
    """Settings 安全校验测试。"""

    def test_production_with_default_jwt_secret_raises(self) -> None:
        """生产环境使用默认 JWT_SECRET_KEY 时应启动失败。"""
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(APP_ENV="production", JWT_SECRET_KEY=SecretStr("changeme"), _env_file=None)

    def test_production_with_short_jwt_secret_raises(self) -> None:
        """生产环境 JWT_SECRET_KEY 长度不足 32 字符时应启动失败。"""
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(APP_ENV="production", JWT_SECRET_KEY=SecretStr("short"), _env_file=None)

    def test_production_with_strong_jwt_secret_passes(self) -> None:
        """生产环境配置足够长度的 JWT_SECRET_KEY 时应正常启动。"""
        settings = Settings(
            APP_ENV="production",
            JWT_SECRET_KEY=SecretStr("a-very-strong-secret-key-that-is-at-least-32-chars-long"),
            _env_file=None,
        )
        assert settings.APP_ENV == "production"

    def test_development_with_default_jwt_secret_passes(self) -> None:
        """开发环境允许使用默认 JWT_SECRET_KEY。"""
        settings = Settings(APP_ENV="development", JWT_SECRET_KEY=SecretStr("changeme"), _env_file=None)
        assert settings.JWT_SECRET_KEY.get_secret_value() == "changeme"

    def test_staging_with_default_jwt_secret_raises(self) -> None:
        """Staging 环境也不允许使用默认 JWT_SECRET_KEY。"""
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(APP_ENV="staging", JWT_SECRET_KEY=SecretStr("changeme"), _env_file=None)

    def test_cors_wildcard_origin_raises(self) -> None:
        """CORS_ALLOWED_ORIGINS 包含通配符 '*' 时应启动失败。"""
        with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS"):
            Settings(CORS_ALLOWED_ORIGINS=["*"], _env_file=None)

    def test_cors_wildcard_among_others_raises(self) -> None:
        """CORS_ALLOWED_ORIGINS 混入通配符 '*' 时应启动失败。"""
        with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS"):
            Settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000", "*"], _env_file=None)

    def test_cors_specific_origins_passes(self) -> None:
        """CORS_ALLOWED_ORIGINS 配置具体域名时应正常启动。"""
        settings = Settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"], _env_file=None)
        assert settings.CORS_ALLOWED_ORIGINS == ["http://localhost:3000"]


@pytest.mark.unit
class TestBedrockKBSettings:
    """Bedrock Knowledge Base 配置字段测试。"""

    def test_kb_defaults_empty_string(self) -> None:
        """开发环境 KB 配置默认为空字符串。"""
        settings = Settings(_env_file=None)
        assert settings.BEDROCK_KB_ROLE_ARN == ""
        assert settings.BEDROCK_KB_EMBEDDING_MODEL_ARN == ""
        assert settings.BEDROCK_KB_S3_BUCKET == ""
        assert settings.BEDROCK_KB_COLLECTION_ARN == ""

    def test_kb_configurable(self) -> None:
        """KB 配置可通过构造参数设置。"""
        settings = Settings(
            BEDROCK_KB_ROLE_ARN="arn:aws:iam::123:role/test",
            BEDROCK_KB_EMBEDDING_MODEL_ARN="arn:aws:bedrock:us-east-1::foundation-model/titan",
            BEDROCK_KB_S3_BUCKET="my-kb-bucket",
            BEDROCK_KB_COLLECTION_ARN="arn:aws:aoss:us-east-1:123:collection/col1",
            _env_file=None,
        )
        assert settings.BEDROCK_KB_ROLE_ARN == "arn:aws:iam::123:role/test"
        assert settings.BEDROCK_KB_EMBEDDING_MODEL_ARN.endswith("titan")
        assert settings.BEDROCK_KB_S3_BUCKET == "my-kb-bucket"
        assert settings.BEDROCK_KB_COLLECTION_ARN.endswith("col1")


@pytest.mark.unit
class TestSecretsManagerIntegration:
    """Settings + Secrets Manager 集成测试。"""

    def test_development_env_skips_secrets_manager(self) -> None:
        """开发环境不调用 Secrets Manager, 即使配置了 ARN。"""
        settings = Settings(
            APP_ENV="development",
            DB_SECRET_ARN="arn:aws:secretsmanager:us-east-1:123:secret:test",
            _env_file=None,
        )
        # 开发环境保持默认值
        assert settings.DATABASE_USER == "root"
        assert settings.DATABASE_PASSWORD.get_secret_value() == "changeme"

    def test_test_env_skips_secrets_manager(self) -> None:
        """测试环境不调用 Secrets Manager。"""
        settings = Settings(
            APP_ENV="test",
            DB_SECRET_ARN="arn:test",
            JWT_SECRET_ARN="arn:jwt",
            _env_file=None,
        )
        assert settings.DATABASE_USER == "root"

    @patch("src.shared.infrastructure.secrets_client.fetch_database_credentials")
    def test_deployed_env_resolves_db_secret(self, mock_fetch_db) -> None:
        """部署环境下配置 DB_SECRET_ARN 时从 Secrets Manager 获取凭证。"""
        mock_fetch_db.return_value = DatabaseCredentials(
            username="sm_user",
            password="sm_password_long_enough_for_test",
            dbname="sm_db",
            host="sm-host.cluster.amazonaws.com",
            port=3306,
        )
        settings = Settings(
            APP_ENV="staging",
            AWS_REGION="ap-northeast-1",
            DB_SECRET_ARN="arn:aws:secretsmanager:ap-northeast-1:123:secret:db",
            JWT_SECRET_KEY=SecretStr("a-very-strong-secret-key-that-is-at-least-32-chars-long"),
            _env_file=None,
        )
        assert settings.DATABASE_USER == "sm_user"
        assert settings.DATABASE_PASSWORD.get_secret_value() == "sm_password_long_enough_for_test"
        assert settings.DATABASE_NAME == "sm_db"
        assert settings.DATABASE_HOST == "sm-host.cluster.amazonaws.com"
        mock_fetch_db.assert_called_once_with(
            "arn:aws:secretsmanager:ap-northeast-1:123:secret:db",
            "ap-northeast-1",
        )

    @patch("src.shared.infrastructure.secrets_client.fetch_jwt_credentials")
    def test_deployed_env_resolves_jwt_secret(self, mock_fetch_jwt) -> None:
        """部署环境下配置 JWT_SECRET_ARN 时从 Secrets Manager 获取 JWT 密钥。"""
        mock_fetch_jwt.return_value = JwtCredentials(
            secret_key="sm-jwt-key-that-is-very-long-and-secure-at-least-32-chars",
        )
        settings = Settings(
            APP_ENV="production",
            AWS_REGION="ap-northeast-1",
            JWT_SECRET_ARN="arn:aws:secretsmanager:ap-northeast-1:123:secret:jwt",
            _env_file=None,
        )
        assert settings.JWT_SECRET_KEY.get_secret_value() == "sm-jwt-key-that-is-very-long-and-secure-at-least-32-chars"
        mock_fetch_jwt.assert_called_once_with(
            "arn:aws:secretsmanager:ap-northeast-1:123:secret:jwt",
            "ap-northeast-1",
        )

    def test_deployed_env_without_arn_uses_env_vars(self) -> None:
        """部署环境下未配置 ARN 时使用环境变量 (ECS Secrets 注入路径)。"""
        settings = Settings(
            APP_ENV="production",
            DATABASE_USER="ecs_user",
            DATABASE_PASSWORD=SecretStr("ecs_password"),
            DATABASE_NAME="ecs_db",
            JWT_SECRET_KEY=SecretStr("a-very-strong-secret-key-that-is-at-least-32-chars-long"),
            _env_file=None,
        )
        assert settings.DATABASE_USER == "ecs_user"
        assert settings.DATABASE_PASSWORD.get_secret_value() == "ecs_password"

    def test_secret_arn_defaults_empty(self) -> None:
        """ARN 字段默认为空字符串。"""
        settings = Settings(_env_file=None)
        assert settings.DB_SECRET_ARN == ""
        assert settings.JWT_SECRET_ARN == ""

    @patch("src.shared.infrastructure.secrets_client.fetch_database_credentials")
    def test_db_secret_host_not_overwritten_when_empty(self, mock_fetch_db) -> None:
        """Secret 中 host 为空时保留原有 DATABASE_HOST。"""
        mock_fetch_db.return_value = DatabaseCredentials(
            username="user",
            password="pw",
            dbname="db",
            host="",
            port=0,
        )
        settings = Settings(
            APP_ENV="dev",
            DATABASE_HOST="original-host",
            DB_SECRET_ARN="arn:db",
            JWT_SECRET_KEY=SecretStr("a-very-strong-secret-key-that-is-at-least-32-chars-long"),
            _env_file=None,
        )
        assert settings.DATABASE_HOST == "original-host"


@pytest.mark.unit
class TestGetSettings:
    def test_get_settings_returns_settings_instance(self):
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)
        get_settings.cache_clear()

    def test_get_settings_is_cached(self):
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        get_settings.cache_clear()
