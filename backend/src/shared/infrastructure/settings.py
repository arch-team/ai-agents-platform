"""应用配置管理。"""

from functools import lru_cache
from typing import Self

from pydantic import SecretStr, model_validator
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

    # AgentCore 配置
    AGENTCORE_GATEWAY_URL: str = ""  # AgentCore Gateway MCP 端点 (SSE URL)

    # Bedrock Knowledge Base 配置 (开发环境允许为空)
    BEDROCK_KB_ROLE_ARN: str = ""
    BEDROCK_KB_EMBEDDING_MODEL_ARN: str = ""
    BEDROCK_KB_S3_BUCKET: str = ""
    BEDROCK_KB_COLLECTION_ARN: str = ""  # OpenSearch Serverless 集合 ARN

    # Refresh Token
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 注册开关 (REGISTRATION_ENABLED=False 时禁用公开注册)
    REGISTRATION_ENABLED: bool = True

    # 登录安全
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 30

    # 数据库连接池
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Bedrock 线程池
    BEDROCK_THREAD_POOL_SIZE: int = 50

    # 对话上下文窗口
    MAX_CONTEXT_TOKENS: int = 30000
    SYSTEM_PROMPT_TOKEN_BUDGET: int = 2000

    # 日志
    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def _validate_secrets(self) -> Self:
        """非开发环境校验密钥安全性，fail-fast 防止弱密钥上线。"""
        if self.APP_ENV not in ("development", "test"):
            jwt_secret = self.JWT_SECRET_KEY.get_secret_value()
            if jwt_secret == "changeme" or len(jwt_secret) < 32:  # noqa: S105
                msg = "JWT_SECRET_KEY 在非开发环境下不能使用默认值且长度不得少于 32 字符"
                raise ValueError(msg)
        # CORS 校验: 禁止通配符 (防止 allow_credentials=True + allow_origins=["*"])
        if "*" in self.CORS_ALLOWED_ORIGINS:
            msg = "CORS_ALLOWED_ORIGINS 不允许包含通配符 '*'"
            raise ValueError(msg)
        return self

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
