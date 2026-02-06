# 安全规范 (Security Standards)

> **职责**: 安全规范，定义禁止事项、必须事项和安全检测命令。基于 OWASP Top 10 和行业最佳实践的 Python 后端安全规范。

---

## 0. 速查卡片

> Claude 生成代码时优先查阅此章节

### 安全规则速查表

| 规则 | ❌ 禁止 | ✅ 正确 |
|------|--------|--------|
| 硬编码密钥 | `API_KEY = "sk-xxx"` | `settings.api_key` (环境变量) |
| SQL 注入 | `f"SELECT * WHERE id='{x}'"` | `session.query().filter()` |
| 命令注入 | `os.system(user_input)` | 参数化命令或白名单 |
| 路径遍历 | `open(f"/uploads/{name}")` | `Path(name).name` 验证 |
| 敏感日志 | `logger.info(f"密码: {pwd}")` | 仅记录非敏感信息 |
| 危险函数 | `eval(user_input)` | `json.loads()` / Pydantic |

### 安全检测命令

```bash
# 完整安全检查
uv run bandit -r src/ && uv run safety check && uv run pip-audit
```

### PR Review 检查清单

详见 [Section 4 检查清单](#4-检查清单)，包含代码审查和部署检查项。

---

## 1. 核心原则

| 原则 | 说明 |
|------|------|
| **最小权限** | 只授予完成任务所需的最小权限 |
| **深度防御** | 多层安全措施，不依赖单一防线 |
| **安全默认** | 默认配置应该是安全的 |
| **失败安全** | 出错时拒绝访问而非放行 |

---

## 2. 禁止事项 (絶対禁止)

### 2.1 硬编码敏感信息

```python
# ❌ 禁止
AWS_SECRET = "wJalrXUtnFEMI..."
API_KEY = "sk-1234567890"

# ✅ 正确 - 见 3.1 节 Settings 模式
settings.aws_secret  # 从环境变量加载
```

**检测**: `grep -rE "(password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]" src/`

### 2.2 注入攻击 (SQL/命令)

```python
# ❌ 禁止 - SQL 注入
query = f"SELECT * FROM users WHERE id = '{user_id}'"
db.execute(query)

# ❌ 禁止 - 命令注入
os.system(user_input)

# ✅ 正确 - ORM 参数化
session.query(User).filter(User.id == user_id).first()

# ✅ 正确 - 原生 SQL 参数绑定
from sqlalchemy import text
stmt = text("SELECT * FROM users WHERE id = :user_id")
session.execute(stmt, {"user_id": user_id})
```

**检测**: `grep -rE "f['\"].*SELECT|os\.system|subprocess\.call.*shell=True" src/`

### 2.3 路径遍历

```python
# ❌ 禁止
return FileResponse(f"/uploads/{filename}")  # 可能访问 ../../../etc/passwd

# ✅ 正确
safe_name = Path(filename).name  # 移除 ../ 等路径组件
file_path = Path("/uploads") / safe_name
if not file_path.is_relative_to(Path("/uploads")):
    raise HTTPException(400, "非法路径")
```

### 2.4 敏感日志

```python
# ❌ 禁止
logger.info(f"用户登录: {username}, 密码: {password}")
logger.debug(f"API 密钥: {api_key}")

# ✅ 正确
logger.info(f"用户登录: {username}")
logger.debug(f"API 密钥: {api_key[:4]}****")  # 脱敏
```

**检测**: `grep -rE "logger\.(info|debug|error).*password" src/`

### 2.5 危险函数

```python
# ❌ 禁止
eval(user_input)           # 远程代码执行
exec(user_code)            # 远程代码执行
pickle.loads(untrusted)    # 反序列化漏洞

# ✅ 正确
import json
data = json.loads(request.body)

# ✅ 正确 - Pydantic 验证
from pydantic import BaseModel
class UserInput(BaseModel):
    name: str
    value: int
data = UserInput.model_validate_json(request.body)
```

**检测**: `grep -rE "\beval\s*\(|\bexec\s*\(|pickle\.loads" src/`

---

## 3. 必须事项 (強制要求)

### 3.1 环境变量配置

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: SecretStr = Field(..., description="数据库连接字符串")
    jwt_secret_key: SecretStr = Field(..., description="JWT 签名密钥")
    aws_secret_access_key: SecretStr = Field(...)
```

### 3.2 输入验证 (Pydantic)

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v): raise ValueError("需要大写字母")
        if not re.search(r"[a-z]", v): raise ValueError("需要小写字母")
        if not re.search(r"\d", v): raise ValueError("需要数字")
        return v
```

### 3.3 密码哈希

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### 3.4 认证模式

```python
# 关键模式: 登录限制 + JWT
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 30

# 检查锁定 → 验证密码 → 重置计数器
# 失败时记录尝试，达到阈值则锁定账户
```

### 3.5 错误处理 (不暴露内部信息)

```python
# 内部日志: 详细记录
logger.error("unhandled_exception", error=str(e), traceback=traceback.format_exc())

# 外部响应: 通用信息
return JSONResponse(
    status_code=500,
    content={"code": "INTERNAL_ERROR", "message": "服务器内部错误"}
    # ❌ 不返回: detail=str(e), traceback=...
)
```

### 3.6 访问控制

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # 验证 token，失败返回 401
    ...

def require_role(roles: list[str]):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "权限不足")
        return user
    return checker
```

---

## 4. 检查清单

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
