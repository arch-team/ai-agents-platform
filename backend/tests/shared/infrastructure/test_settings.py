"""Settings 配置管理测试。"""

import pytest
from pydantic import SecretStr

from src.shared.infrastructure.settings import Settings, get_settings


@pytest.mark.unit
class TestSettings:
    def test_default_app_name(self):
        settings = Settings()
        assert settings.APP_NAME == "ai-agents-platform"

    def test_default_app_env(self):
        settings = Settings()
        assert settings.APP_ENV == "development"

    def test_default_debug_false(self):
        settings = Settings()
        assert settings.APP_DEBUG is False

    def test_database_defaults(self):
        settings = Settings()
        assert settings.DATABASE_HOST == "localhost"
        assert settings.DATABASE_PORT == 3306
        assert settings.DATABASE_NAME == "ai_agents_platform"
        assert settings.DATABASE_USER == "root"

    def test_database_password_is_secret(self):
        settings = Settings(DATABASE_PASSWORD=SecretStr("my-secret-pw"))
        assert isinstance(settings.DATABASE_PASSWORD, SecretStr)
        assert settings.DATABASE_PASSWORD.get_secret_value() == "my-secret-pw"

    def test_database_password_default(self):
        settings = Settings()
        assert settings.DATABASE_PASSWORD.get_secret_value() == "changeme"

    def test_jwt_defaults(self):
        settings = Settings()
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_jwt_secret_key_is_secret(self):
        settings = Settings(JWT_SECRET_KEY=SecretStr("my-jwt-secret"))
        assert isinstance(settings.JWT_SECRET_KEY, SecretStr)
        assert settings.JWT_SECRET_KEY.get_secret_value() == "my-jwt-secret"

    def test_aws_region_configurable(self):
        settings = Settings(AWS_REGION="ap-northeast-1")
        assert settings.AWS_REGION == "ap-northeast-1"

    def test_log_level_default(self):
        settings = Settings()
        assert settings.LOG_LEVEL == "INFO"

    def test_database_url_property(self):
        settings = Settings(
            DATABASE_HOST="db-host",
            DATABASE_PORT=3307,
            DATABASE_NAME="testdb",
            DATABASE_USER="testuser",
            DATABASE_PASSWORD=SecretStr("testpw"),
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
            Settings(APP_ENV="production", JWT_SECRET_KEY=SecretStr("changeme"))

    def test_production_with_short_jwt_secret_raises(self) -> None:
        """生产环境 JWT_SECRET_KEY 长度不足 32 字符时应启动失败。"""
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(APP_ENV="production", JWT_SECRET_KEY=SecretStr("short"))

    def test_production_with_strong_jwt_secret_passes(self) -> None:
        """生产环境配置足够长度的 JWT_SECRET_KEY 时应正常启动。"""
        settings = Settings(
            APP_ENV="production",
            JWT_SECRET_KEY=SecretStr("a-very-strong-secret-key-that-is-at-least-32-chars-long"),
        )
        assert settings.APP_ENV == "production"

    def test_development_with_default_jwt_secret_passes(self) -> None:
        """开发环境允许使用默认 JWT_SECRET_KEY。"""
        settings = Settings(APP_ENV="development", JWT_SECRET_KEY=SecretStr("changeme"))
        assert settings.JWT_SECRET_KEY.get_secret_value() == "changeme"

    def test_staging_with_default_jwt_secret_raises(self) -> None:
        """Staging 环境也不允许使用默认 JWT_SECRET_KEY。"""
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(APP_ENV="staging", JWT_SECRET_KEY=SecretStr("changeme"))


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
