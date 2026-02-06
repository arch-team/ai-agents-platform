# 代码风格规范 (Code Style)

> **职责**: Python 代码风格规范，定义类型提示、命名和 Docstring 原则。本文档定义 Python 后端项目的代码风格规范，基于 PEP 8 并结合现代 Python 最佳实践。

---

## 0. 速查卡片

> Claude 生成代码时优先查阅此章节

### 类型提示速查
| 规则 | 示例 |
|------|------|
| ✅ 所有公共接口必须有类型提示 | `def get_user(user_id: int) -> User \| None:` |
| ✅ 使用 `X \| None` 代替 `Optional[X]` | `name: str \| None = None` |
| ✅ 使用内置泛型 (Python 3.9+) | `list[str]`, `dict[str, int]` |
| ❌ 禁止使用 `Any` | 使用 `TypeVar` 或具体类型替代 |

### 命名速查
| 元素 | 样式 | 示例 |
|------|------|------|
| 函数/变量 | `snake_case` | `get_user_by_id` |
| 类 | `PascalCase` | `UserRepository` |
| 常量 | `UPPER_SNAKE` | `MAX_RETRY` |
| 私有 | `_prefix` | `_cache` |
| 类型变量 | `PascalCase` + T | `EntityT` |

### Docstring 速查
```
类型自解释 → 省略 Docstring | 有副作用/异常 → 说明行为
```

### 异步代码速查
```python
# ✅ 正确 - 异步函数
async def fetch_user(user_id: int) -> User: ...

# ✅ 正确 - 上下文管理
async with get_db_session() as session: ...

# ✅ 正确 - 并发执行
results = await asyncio.gather(task1(), task2())
```

### Ruff 自动检查项 (无需人工关注)
- 导入排序 (isort)
- 行长度 120 字符
- 空行规范
- 格式化风格

---

## 1. 类型提示 (Type Hints)

所有公共接口必须包含完整的类型提示。

```python
# ✅ 正确 - 完整类型提示
def get_user(user_id: int) -> User | None:
    """根据 ID 获取用户。"""
    ...

async def fetch_data(url: str, timeout: float = 30.0) -> bytes:
    """异步获取数据。"""
    ...

# ✅ 正确 - 泛型类
T = TypeVar("T")

class Repository(Generic[T]):
    def get(self, id: int) -> T | None: ...
    def save(self, entity: T) -> T: ...

# ❌ 错误 - 缺少类型提示
def get_user(user_id):
    ...
```

---

## 2. 命名规范

### 命名样式汇总

| 元素 | 样式 | 示例 |
|------|------|------|
| 模块/包 | `snake_case` | `user_repository.py` |
| 类 | `PascalCase` | `UserRepository` |
| 函数/方法 | `snake_case` | `get_user_by_id()` |
| 变量 | `snake_case` | `user_count` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| 类型变量 | `PascalCase` + T | `EntityT`, `ResponseT` |
| 私有成员 | `_leading_underscore` | `_internal_state` |

### 命名原则

1. **清晰优于简洁**: `get_user_by_email()` 优于 `get_user()`
2. **动词开头的方法**: `create_user()`, `validate_input()`, `calculate_total()`
3. **布尔值命名**: `is_active`, `has_permission`, `can_edit`
4. **集合命名使用复数**: `users`, `items`, `training_jobs`

---

## 3. Docstring 规范

### 核心原则

> **类型即文档**: 类型提示 + 好命名 = 自解释代码。Docstring 只写类型无法表达的内容。

### 写与不写

| 场景 | 要求 |
|------|------|
| 类/模块 | ✅ 一句话描述职责 |
| 方法 - 类型自解释 | ❌ 省略 |
| 方法 - 有副作用/异常 | ✅ 说明行为 |
| 私有方法 | ❌ 省略 |

### 示例

```python
# ❌ 冗余 - 类型已自解释
def get_user(user_id: int) -> User | None:
    """根据 ID 获取用户。
    Args: user_id: 用户 ID
    Returns: 用户实体或 None
    """

# ✅ 正确 - 省略多余注释
def get_user(user_id: int) -> User | None: ...

# ✅ 必要 - 有副作用和异常需说明
def create_user(dto: CreateUserDTO) -> User:
    """创建用户并发送欢迎邮件。
    Raises: ValidationError, DuplicateEmailError
    """

class UserService:
    """用户业务服务。"""  # 类只需一句话
```

---

## 4. 异步代码规范 (Async Patterns)

### 异步函数定义

```python
# ✅ 正确 - 显式 async
async def get_user(user_id: int) -> User | None:
    async with self._session_factory() as session:
        return await session.get(User, user_id)

# ❌ 错误 - 同步阻塞调用
def get_user(user_id: int) -> User | None:
    return asyncio.run(self._fetch_user(user_id))  # 禁止在已有事件循环中使用
```

### 并发执行

```python
# ✅ 正确 - asyncio.gather 并发执行独立任务
user, permissions = await asyncio.gather(
    fetch_user(user_id),
    fetch_permissions(user_id),
)

# ❌ 错误 - 可并行时顺序执行
user = await fetch_user(user_id)
permissions = await fetch_permissions(user_id)  # 浪费时间
```

### 异步上下文管理

```python
# ✅ 正确 - 异步上下文管理器
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()

# ✅ 正确 - 数据库会话
async with async_session() as session:
    async with session.begin():
        session.add(entity)
```

---

## 5. 导入规范

```python
# 1. 标准库导入
import os
from collections.abc import Callable
from typing import TypeVar

# 2. 第三方库导入
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 3. 本地应用导入
from src.domain.entities import User
from src.application.dto import CreateUserDTO
```

**规则**:
- ✅ 具体导入: `from src.domain.entities import User`
- ❌ 通配符导入: `from src.domain.entities import *`
- ✅ 长路径别名: `from src.infrastructure.external.aws import sagemaker_client as sagemaker`

---

## 6. 代码组织

### 类内部组织顺序

```python
class UserService:
    """用户服务类。"""

    # 1. 类常量
    MAX_LOGIN_ATTEMPTS = 5

    # 2. __init__ 方法
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    # 3. 特殊方法 (__str__, __repr__, __eq__ 等)
    def __repr__(self) -> str:
        return f"UserService(repository={self._repository})"

    # 4. 类方法 (@classmethod)
    @classmethod
    def from_config(cls, config: Config) -> "UserService": ...

    # 5. 静态方法 (@staticmethod)
    @staticmethod
    def validate_email(email: str) -> bool: ...

    # 6. 属性 (@property)
    @property
    def repository(self) -> UserRepository:
        return self._repository

    # 7. 公共方法
    def create_user(self, dto: CreateUserDTO) -> User: ...

    # 8. 私有方法
    def _validate_user_data(self, data: dict) -> None: ...
```

### 函数长度和复杂度

- **函数行数**: 建议不超过 50 行
- **圈复杂度**: 建议不超过 10
- **参数数量**: 建议不超过 5 个 (超过时使用数据类封装)

```python
# ✅ 正确 - 使用数据类封装多参数
@dataclass
class CreateUserDTO:
    name: str
    email: str
    password: str
    phone: str | None = None

def create_user(dto: CreateUserDTO) -> User: ...
```

---

## 7. 错误处理

### 异常定义

```python
# src/domain/exceptions.py
class DomainError(Exception):
    """领域层基础异常类。"""
    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code

class ValidationError(DomainError): pass      # HTTP 422
class EntityNotFoundError(DomainError): pass  # HTTP 404
class DuplicateEntityError(DomainError): pass # HTTP 409
```

### 异常处理最佳实践

```python
# ✅ 正确 - 捕获具体异常
try:
    user = repository.get_by_id(user_id)
except EntityNotFoundError:
    logger.warning(f"用户 {user_id} 不存在")
    raise
except DatabaseConnectionError as e:
    logger.error(f"数据库连接失败: {e}")
    raise ServiceUnavailableError("服务暂时不可用") from e

# ❌ 错误 - 捕获所有异常并静默忽略
try:
    user = repository.get_by_id(user_id)
except Exception:
    pass
```

---

## 检查清单

在 PR Review 时，检查以下代码风格要点：

- [ ] 所有公共接口都有类型提示
- [ ] 没有使用 `Any` 类型
- [ ] 命名符合规范 (snake_case/PascalCase)
- [ ] Docstring 遵循"类型即文档"原则 (类型自解释时省略)
- [ ] 导入按正确顺序组织
- [ ] 没有通配符导入
- [ ] 异常处理具体而非宽泛
- [ ] 异步代码正确使用 async/await
- [ ] 函数复杂度在合理范围内
