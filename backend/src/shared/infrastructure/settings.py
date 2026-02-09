"""应用配置管理。"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，从环境变量加载。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # 应用配置
    APP_NAME: str = "ai-agents-platform"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False

    # 数据库配置
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_NAME: str = "ai_agents_platform"
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: SecretStr = SecretStr("changeme")

    # JWT 认证
    JWT_SECRET_KEY: SecretStr = SecretStr("changeme")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS 配置 — 生产环境必须配置具体域名
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # AWS 配置
    AWS_REGION: str = "us-east-1"

    # Bedrock 配置
    BEDROCK_DEFAULT_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # 日志
    LOG_LEVEL: str = "INFO"

    @property
    def database_url(self) -> str:
        """构建 asyncmy 数据库连接字符串。"""
        pwd = self.DATABASE_PASSWORD.get_secret_value()
        return (
            f"mysql+asyncmy://{self.DATABASE_USER}:{pwd}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例。"""
    return Settings()
