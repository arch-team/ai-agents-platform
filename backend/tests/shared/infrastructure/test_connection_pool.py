"""数据库连接池和 Bedrock 线程池配置测试。"""

import inspect

import pytest

from src.shared.infrastructure.database import init_db
from src.shared.infrastructure.settings import Settings


@pytest.mark.unit
class TestInitDbPoolParams:
    """init_db 接受连接池参数。"""

    def test_init_db_signature_has_pool_params(self) -> None:
        """init_db 函数签名包含 pool_size, max_overflow, pool_timeout, pool_recycle 参数。"""
        sig = inspect.signature(init_db)
        param_names = list(sig.parameters.keys())
        assert "pool_size" in param_names
        assert "max_overflow" in param_names
        assert "pool_timeout" in param_names
        assert "pool_recycle" in param_names

    def test_init_db_pool_defaults(self) -> None:
        """init_db 连接池参数默认值正确。"""
        sig = inspect.signature(init_db)
        assert sig.parameters["pool_size"].default == 20
        assert sig.parameters["max_overflow"].default == 30
        assert sig.parameters["pool_timeout"].default == 30
        assert sig.parameters["pool_recycle"].default == 1800


@pytest.mark.unit
class TestSettingsPoolConfig:
    """Settings 包含连接池配置项。"""

    def test_settings_has_db_pool_config(self) -> None:
        """Settings 包含数据库连接池配置。"""
        settings = Settings()
        assert settings.DB_POOL_SIZE == 20
        assert settings.DB_MAX_OVERFLOW == 30
        assert settings.DB_POOL_TIMEOUT == 30
        assert settings.DB_POOL_RECYCLE == 1800

    def test_settings_has_bedrock_thread_pool_config(self) -> None:
        """Settings 包含 Bedrock 线程池配置。"""
        settings = Settings()
        assert settings.BEDROCK_THREAD_POOL_SIZE == 50

    def test_settings_has_registration_enabled(self) -> None:
        """Settings 包含注册开关配置。"""
        settings = Settings()
        assert settings.REGISTRATION_ENABLED is True
