# 安全规范 (Security Standards)

本文档定义 Python 后端项目的安全规范，基于 OWASP Top 10 和行业最佳实践。

---

## 安全原则

### 核心原则

| 原则 | 说明 |
|------|------|
| **最小权限** | 只授予完成任务所需的最小权限 |
| **深度防御** | 多层安全措施，不依赖单一防线 |
| **安全默认** | 默认配置应该是安全的 |
| **失败安全** | 出错时拒绝访问而非放行 |

---

## 禁止事项 (絶対禁止)

### 1. 硬编码敏感信息

```python
# ❌ 絶对禁止 - 硬编码密钥
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DATABASE_PASSWORD = "my_secret_password"
API_KEY = "sk-1234567890abcdef"

# ✅ 正确 - 使用环境变量
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aws_access_key: str
    aws_secret_key: str
    database_password: str
    api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 2. SQL 字符串拼接

```python
# ❌ 絶对禁止 - SQL 注入漏洞
def get_user(user_id: str) -> dict:
    query = f"SELECT * FROM users WHERE id = '{user_id}'"  # 危险！
    return db.execute(query)

# ❌ 絶对禁止 - 格式化字符串
query = "SELECT * FROM users WHERE id = '%s'" % user_id

# ✅ 正确 - 使用参数化查询
def get_user(user_id: str) -> User | None:
    return session.query(User).filter(User.id == user_id).first()

# ✅ 正确 - 原生 SQL 使用参数绑定
from sqlalchemy import text
query = text("SELECT * FROM users WHERE id = :user_id")
result = session.execute(query, {"user_id": user_id})
```

### 3. 未验证的用户输入

```python
# ❌ 絶对禁止 - 直接使用未验证输入
@router.get("/files/{filename}")
def get_file(filename: str):
    return FileResponse(f"/uploads/{filename}")  # 路径遍历漏洞！

# ❌ 絶对禁止 - 直接执行用户输入
def run_command(cmd: str):
    os.system(cmd)  # 命令注入！

# ✅ 正确 - 验证和清理输入
from pathlib import Path

@router.get("/files/{filename}")
def get_file(filename: str):
    # 验证文件名
    safe_filename = Path(filename).name  # 移除路径组件
    if not safe_filename or safe_filename.startswith("."):
        raise HTTPException(status_code=400, detail="无效的文件名")

    file_path = Path("/uploads") / safe_filename
    if not file_path.is_relative_to(Path("/uploads")):
        raise HTTPException(status_code=400, detail="非法路径")

    return FileResponse(file_path)
```

### 4. 敏感信息日志

```python
# ❌ 絶对禁止 - 记录敏感信息
logger.info(f"用户登录: {username}, 密码: {password}")
logger.debug(f"API 密钥: {api_key}")
logger.info(f"信用卡号: {card_number}")

# ✅ 正确 - 脱敏后记录
logger.info(f"用户登录: {username}")
logger.debug(f"API 密钥: {api_key[:4]}****{api_key[-4:]}")
logger.info(f"信用卡号: ****{card_number[-4:]}")

# ✅ 正确 - 使用结构化日志并排除敏感字段
import structlog

logger = structlog.get_logger()
logger.info(
    "user_login",
    username=username,
    ip_address=request.client.host,
    # 不记录密码
)
```

### 5. 危险函数

```python
# ❌ 絶对禁止 - eval/exec
user_code = request.json.get("code")
result = eval(user_code)  # 远程代码执行！

# ❌ 絶对禁止 - pickle 反序列化不可信数据
import pickle
data = pickle.loads(request.body)  # 反序列化漏洞！

# ✅ 正确 - 使用 JSON 序列化
import json
data = json.loads(request.body)

# ✅ 正确 - 使用 Pydantic 验证
from pydantic import BaseModel

class UserInput(BaseModel):
    name: str
    value: int

data = UserInput.model_validate_json(request.body)
```

---

## 必须事项 (強制要求)

### 1. 环境变量管理敏感配置

```python
# src/infrastructure/config/settings.py

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。

    所有敏感配置从环境变量加载。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 数据库
    database_url: SecretStr = Field(..., description="数据库连接字符串")

    # AWS
    aws_access_key_id: SecretStr = Field(..., description="AWS 访问密钥 ID")
    aws_secret_access_key: SecretStr = Field(..., description="AWS 秘密访问密钥")
    aws_region: str = Field(default="us-west-2", description="AWS 区域")

    # JWT
    jwt_secret_key: SecretStr = Field(..., description="JWT 签名密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT 算法")
    jwt_expire_minutes: int = Field(default=30, description="JWT 过期时间(分钟)")

    def get_database_url(self) -> str:
        """获取数据库 URL (脱敏)。"""
        return self.database_url.get_secret_value()
```

### 2. 输入验证

```python
# src/presentation/schemas/user_schemas.py

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class CreateUserRequest(BaseModel):
    """创建用户请求。"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="用户名称",
    )
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="用户密码",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证名称格式。"""
        # 移除首尾空白
        v = v.strip()
        # 检查是否只包含允许的字符
        if not re.match(r"^[\w\s\u4e00-\u9fff]+$", v):
            raise ValueError("名称包含非法字符")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度。"""
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含小写字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("密码必须包含特殊字符")
        return v
```

### 3. 密码哈希

```python
# src/infrastructure/security/password.py

from passlib.context import CryptContext

# 使用 bcrypt 算法
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # 成本因子
)


def hash_password(password: str) -> str:
    """对密码进行哈希。

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)
```

### 4. JWT 认证

```python
# src/infrastructure/security/jwt.py

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from src.infrastructure.config import Settings


class JWTHandler:
    """JWT 处理器。"""

    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.jwt_secret_key.get_secret_value()
        self._algorithm = settings.jwt_algorithm
        self._expire_minutes = settings.jwt_expire_minutes

    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """创建访问令牌。

        Args:
            data: 令牌载荷
            expires_delta: 过期时间增量

        Returns:
            JWT 令牌
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=self._expire_minutes)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict[str, Any]:
        """解码令牌。

        Args:
            token: JWT 令牌

        Returns:
            令牌载荷

        Raises:
            JWTError: 令牌无效时
        """
        return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
```

### 5. 错误处理 (不暴露内部信息)

```python
# src/presentation/api/middleware/error_handler.py

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全局错误处理中间件。"""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            # 记录详细错误信息 (内部日志)
            logger.error(
                "unhandled_exception",
                error=str(e),
                traceback=traceback.format_exc(),
                path=request.url.path,
                method=request.method,
            )

            # 返回通用错误信息 (不暴露内部细节)
            return JSONResponse(
                status_code=500,
                content={
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误，请稍后重试",
                    # ❌ 不要返回: "detail": str(e)
                    # ❌ 不要返回: "traceback": traceback.format_exc()
                },
            )
```

---

## OWASP Top 10 防护

### A01: 访问控制缺陷

```python
# src/presentation/api/dependencies/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.domain.entities import User
from src.application.interfaces import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """获取当前认证用户。"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user = auth_service.verify_token(token)
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception


def require_role(required_roles: list[str]):
    """角色权限装饰器。"""
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return current_user
    return role_checker


# 使用示例
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
):
    """删除用户 (仅管理员)。"""
    ...
```

### A03: 注入攻击

```python
# 使用 SQLAlchemy ORM 防止 SQL 注入
def search_users(query: str) -> list[User]:
    """搜索用户。"""
    # ✅ 安全 - 使用 ORM
    return session.query(UserModel).filter(
        UserModel.name.ilike(f"%{query}%")
    ).all()


# 如果必须使用原生 SQL
from sqlalchemy import text

def raw_search(query: str) -> list[dict]:
    """原生 SQL 搜索。"""
    # ✅ 安全 - 使用参数绑定
    stmt = text("SELECT * FROM users WHERE name LIKE :query")
    return session.execute(stmt, {"query": f"%{query}%"}).fetchall()
```

### A07: 认证缺陷

```python
# src/infrastructure/security/auth.py

from datetime import datetime, timedelta
import secrets

from src.domain.repositories import UserRepository
from src.infrastructure.security.password import verify_password


class AuthService:
    """认证服务。"""

    # 登录尝试限制
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository
        self._login_attempts: dict[str, list[datetime]] = {}

    def authenticate(self, email: str, password: str) -> User | None:
        """认证用户。"""
        # 1. 检查是否被锁定
        if self._is_locked_out(email):
            raise AuthenticationError("账户已被锁定，请稍后重试")

        # 2. 获取用户
        user = self._user_repository.get_by_email(email)
        if not user:
            self._record_failed_attempt(email)
            return None

        # 3. 验证密码
        if not verify_password(password, user.password_hash):
            self._record_failed_attempt(email)
            return None

        # 4. 重置登录尝试
        self._reset_attempts(email)
        return user

    def _is_locked_out(self, email: str) -> bool:
        """检查是否被锁定。"""
        attempts = self._login_attempts.get(email, [])
        cutoff = datetime.utcnow() - timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
        recent_attempts = [a for a in attempts if a > cutoff]
        return len(recent_attempts) >= self.MAX_LOGIN_ATTEMPTS

    def _record_failed_attempt(self, email: str) -> None:
        """记录失败尝试。"""
        if email not in self._login_attempts:
            self._login_attempts[email] = []
        self._login_attempts[email].append(datetime.utcnow())

    def _reset_attempts(self, email: str) -> None:
        """重置登录尝试。"""
        self._login_attempts.pop(email, None)
```

---

## 依赖安全

### 依赖扫描配置

```toml
# pyproject.toml

[tool.bandit]
exclude_dirs = ["tests", "venv"]
skips = ["B101"]  # 跳过 assert 检查 (测试中使用)

[tool.safety]
# 使用 safety check 扫描已知漏洞
```

### 定期检查命令

```bash
# 安全审计
uv run bandit -r src/

# 依赖漏洞扫描
uv run safety check

# 依赖更新检查
uv run pip-audit
```

---

## 安全检查清单

### 代码审查检查项

- [ ] 没有硬编码的密钥或密码
- [ ] 所有用户输入都经过验证
- [ ] 使用参数化查询，没有 SQL 拼接
- [ ] 敏感信息不会写入日志
- [ ] 没有使用 eval/exec/pickle
- [ ] 密码使用安全哈希算法存储
- [ ] JWT 配置正确 (算法、过期时间)
- [ ] 错误响应不暴露内部信息
- [ ] 访问控制检查到位
- [ ] 文件操作有路径验证

### 部署检查项

- [ ] 敏感配置通过环境变量传递
- [ ] HTTPS 已启用
- [ ] CORS 配置正确
- [ ] 安全头部已设置
- [ ] 依赖已更新到安全版本
- [ ] 日志不包含敏感信息
