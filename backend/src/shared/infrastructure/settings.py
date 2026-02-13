"""应用配置管理。

配置读取优先级:
  1. 环境变量 (ECS Secrets Manager 注入、系统环境变量)
  2. .env 文件 (本地开发)
  3. Secrets Manager 直接读取 (部署环境, 当 SECRET_ARN 配置时)

部署环境下 (APP_ENV 不为 development/test), 若配置了 DB_SECRET_ARN 或
JWT_SECRET_ARN, 应用启动时会从 Secrets Manager 获取对应凭证覆盖默认值。
ECS 容器通常已通过 ecs.Secret.fromSecretsManager 注入凭证为环境变量,
此时无需配置 ARN 字段 — 两种方式互为补充。
"""

import logging
from functools import lru_cache
from typing import Self
from urllib.parse import quote_plus

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)


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

    # Secrets Manager ARN — 部署环境下用于直接从 Secrets Manager 读取凭证
    # 为空时跳过 (依赖 ECS Secrets 注入或环境变量)
    DB_SECRET_ARN: str = ""
    JWT_SECRET_ARN: str = ""

    # CORS 配置 — 生产环境必须配置具体域名
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # AWS 配置
    AWS_REGION: str = "us-east-1"

    # Bedrock 配置
    BEDROCK_DEFAULT_MODEL_ID: str = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    # AgentCore 配置
    AGENTCORE_GATEWAY_ID: str = ""  # AgentCore Gateway 资源 ID (用于 Tool 注册/注销)
    AGENTCORE_GATEWAY_URL: str = ""  # AgentCore Gateway MCP 端点 (SSE URL)
    AGENTCORE_MEMORY_ID: str = ""  # AgentCore Memory 资源 ID (可选)

    # Agent 运行时模式: in_process (本地 Claude Agent SDK) / agentcore_runtime (远程 AgentCore API)
    AGENT_RUNTIME_MODE: str = "in_process"

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

    # 团队执行配置
    TEAM_EXECUTION_MAX_TURNS: int = 200
    TEAM_EXECUTION_TIMEOUT_SECONDS: int = 1800
    TEAM_EXECUTION_MAX_CONCURRENT: int = 3

    # SSE 连接限制
    SSE_MAX_CONNECTIONS_PER_USER: int = 5

    # OpenTelemetry 可观测性
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""  # OTLP 导出端点 (如 http://localhost:4317)

    @model_validator(mode="after")
    def _resolve_secrets_manager(self) -> Self:
        """部署环境下从 Secrets Manager 获取凭证覆盖默认值。

        当 DB_SECRET_ARN / JWT_SECRET_ARN 非空且 APP_ENV 为部署环境时,
        调用 Secrets Manager API 读取实际凭证。ECS 容器若已通过 ecs.Secret
        注入环境变量, 则 ARN 字段可留空, 此 validator 跳过。
        """
        from src.shared.infrastructure.secrets_client import is_deployed_env

        if not is_deployed_env(self.APP_ENV):
            return self

        # 数据库凭证
        if self.DB_SECRET_ARN:
            self._resolve_db_secret()

        # JWT 签名密钥
        if self.JWT_SECRET_ARN:
            self._resolve_jwt_secret()

        return self

    def _resolve_db_secret(self) -> None:
        from src.shared.infrastructure.secrets_client import fetch_database_credentials

        logger.info("从 Secrets Manager 读取数据库凭证: %s", self.DB_SECRET_ARN)
        creds = fetch_database_credentials(self.DB_SECRET_ARN, self.AWS_REGION)
        self.DATABASE_USER = creds.username
        self.DATABASE_PASSWORD = SecretStr(creds.password)
        self.DATABASE_NAME = creds.dbname
        if creds.host:
            self.DATABASE_HOST = creds.host
        if creds.port:
            self.DATABASE_PORT = creds.port

    def _resolve_jwt_secret(self) -> None:
        from src.shared.infrastructure.secrets_client import fetch_jwt_credentials

        logger.info("从 Secrets Manager 读取 JWT 密钥: %s", self.JWT_SECRET_ARN)
        creds = fetch_jwt_credentials(self.JWT_SECRET_ARN, self.AWS_REGION)
        self.JWT_SECRET_KEY = SecretStr(creds.secret_key)

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
        """构建 asyncmy 数据库连接字符串。

        对用户名和密码进行 URL 编码，防止特殊字符 (@, /, :) 导致连接字符串解析错误。
        """
        user = quote_plus(self.DATABASE_USER)
        pwd = quote_plus(self.DATABASE_PASSWORD.get_secret_value())
        return f"mysql+asyncmy://{user}:{pwd}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例。"""
    return Settings()
