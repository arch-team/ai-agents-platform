# 代码风格规范 (Code Style)

本文档定义 Python 后端项目的代码风格规范，基于 PEP 8 并结合现代 Python 最佳实践。

---

## 类型提示 (Type Hints)

### 强制要求

所有公共接口必须包含完整的类型提示。

```python
# ✅ 正确 - 完整类型提示
def get_user(user_id: int) -> User | None:
    """根据 ID 获取用户。"""
    ...

def process_items(items: list[str]) -> dict[str, int]:
    """处理项目列表并返回计数字典。"""
    ...

async def fetch_data(url: str, timeout: float = 30.0) -> bytes:
    """异步获取数据。"""
    ...

# ❌ 错误 - 缺少类型提示
def get_user(user_id):
    ...

def process_items(items):
    ...
```

### 类型提示最佳实践

```python
from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar, Generic

# 使用 | 代替 Union (Python 3.10+)
def find_user(user_id: int) -> User | None:
    ...

# 使用内置泛型 (Python 3.9+)
def process_names(names: list[str]) -> dict[str, int]:
    ...

# 可调用对象类型
def apply_transform(
    data: list[int],
    transform: Callable[[int], int]
) -> list[int]:
    ...

# 泛型类
T = TypeVar("T")

class Repository(Generic[T]):
    def get(self, id: int) -> T | None:
        ...

    def save(self, entity: T) -> T:
        ...
```

### 禁止使用 Any

```python
# ❌ 禁止
from typing import Any

def process_data(data: Any) -> Any:
    ...

# ✅ 正确 - 使用具体类型或泛型
from typing import TypeVar

T = TypeVar("T")

def process_data(data: T) -> T:
    ...
```

---

## 命名规范

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
| 魔术方法 | `__double_underscore__` | `__init__`, `__str__` |

### 命名示例

```python
# 模块名
user_service.py
training_job_repository.py

# 类名
class UserService:
    pass

class TrainingJobRepository:
    pass

# 常量
MAX_BATCH_SIZE = 100
DEFAULT_TIMEOUT_SECONDS = 30

# 函数名
def calculate_total_cost(items: list[Item]) -> Decimal:
    pass

def validate_email_format(email: str) -> bool:
    pass

# 私有方法
class UserService:
    def _validate_user_data(self, data: dict) -> None:
        pass

    def __calculate_internal_score(self) -> float:
        # 双下划线用于名称修饰 (name mangling)
        pass
```

### 命名原则

1. **清晰优于简洁**: `get_user_by_email()` 优于 `get_user()`
2. **动词开头的方法**: `create_user()`, `validate_input()`, `calculate_total()`
3. **布尔值命名**: `is_active`, `has_permission`, `can_edit`
4. **集合命名使用复数**: `users`, `items`, `training_jobs`

---

## Docstring 规范 (Google Style)

### 模块级 Docstring

```python
"""用户服务模块。

提供用户相关的业务逻辑处理，包括用户创建、更新、查询等功能。

Example:
    from src.application.services import user_service

    user = user_service.create_user(name="张三", email="zhangsan@example.com")
"""
```

### 类 Docstring

```python
class UserService:
    """用户服务类，处理用户相关的业务逻辑。

    负责用户的创建、更新、删除和查询操作，以及相关的业务规则验证。

    Attributes:
        repository: 用户仓储接口实例
        email_service: 邮件服务实例

    Example:
        service = UserService(repository, email_service)
        user = service.create_user(CreateUserDTO(name="张三"))
    """

    def __init__(
        self,
        repository: UserRepository,
        email_service: EmailService
    ) -> None:
        """初始化用户服务。

        Args:
            repository: 用户仓储接口
            email_service: 邮件服务接口
        """
        self._repository = repository
        self._email_service = email_service
```

### 函数/方法 Docstring

```python
def create_user(self, dto: CreateUserDTO) -> User:
    """创建新用户。

    根据提供的数据创建新用户，并发送欢迎邮件。

    Args:
        dto: 创建用户的数据传输对象，包含用户名、邮箱等信息

    Returns:
        创建成功的用户实体

    Raises:
        ValidationError: 当邮箱格式无效时抛出
        DuplicateEmailError: 当邮箱已被注册时抛出
        EmailSendError: 当发送欢迎邮件失败时抛出

    Example:
        dto = CreateUserDTO(name="张三", email="zhangsan@example.com")
        user = service.create_user(dto)
        print(f"用户 {user.name} 创建成功")
    """
```

### 何时需要 Docstring

| 场景 | 是否必须 |
|------|---------|
| 公共模块 | ✅ 必须 |
| 公共类 | ✅ 必须 |
| 公共方法/函数 | ✅ 必须 |
| 私有方法 (复杂逻辑) | 🟡 推荐 |
| 简单的 getter/setter | ❌ 不需要 |

---

## 导入规范

### 导入顺序

```python
# 1. 标准库导入
import os
import sys
from collections.abc import Callable
from datetime import datetime
from typing import TypeVar

# 2. 第三方库导入
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, String
from sqlalchemy.orm import Session

# 3. 本地应用导入
from src.domain.entities import User
from src.application.dto import CreateUserDTO
from src.infrastructure.database import get_db_session
```

### 导入规则

```python
# ✅ 正确 - 具体导入
from src.domain.entities import User
from src.application.services import UserService

# ❌ 错误 - 通配符导入
from src.domain.entities import *

# ✅ 正确 - 模块别名用于长路径
from src.infrastructure.external.aws import sagemaker_client as sagemaker

# ❌ 错误 - 不必要的别名
from datetime import datetime as dt  # datetime 已经足够短
```

---

## 代码组织

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
    def from_config(cls, config: Config) -> "UserService":
        ...

    # 5. 静态方法 (@staticmethod)
    @staticmethod
    def validate_email(email: str) -> bool:
        ...

    # 6. 属性 (@property)
    @property
    def repository(self) -> UserRepository:
        return self._repository

    # 7. 公共方法
    def create_user(self, dto: CreateUserDTO) -> User:
        ...

    def get_user(self, user_id: int) -> User | None:
        ...

    # 8. 私有方法
    def _validate_user_data(self, data: dict) -> None:
        ...
```

### 函数长度和复杂度

- **函数行数**: 建议不超过 50 行
- **圈复杂度**: 建议不超过 10
- **参数数量**: 建议不超过 5 个

```python
# ❌ 错误 - 过多参数
def create_user(
    name: str,
    email: str,
    password: str,
    phone: str,
    address: str,
    city: str,
    country: str,
    postal_code: str,
) -> User:
    ...

# ✅ 正确 - 使用数据类封装
@dataclass
class CreateUserDTO:
    name: str
    email: str
    password: str
    phone: str | None = None
    address: Address | None = None

def create_user(dto: CreateUserDTO) -> User:
    ...
```

---

## 错误处理

### 异常定义

```python
# src/domain/exceptions.py

class DomainError(Exception):
    """领域层基础异常类。"""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class ValidationError(DomainError):
    """数据验证错误。"""
    pass


class EntityNotFoundError(DomainError):
    """实体未找到错误。"""
    pass


class DuplicateEntityError(DomainError):
    """实体重复错误。"""
    pass
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

# ❌ 错误 - 捕获所有异常
try:
    user = repository.get_by_id(user_id)
except Exception:  # 过于宽泛
    pass  # 静默忽略

# ✅ 正确 - 使用 finally 清理资源
try:
    connection = create_connection()
    result = connection.execute(query)
finally:
    connection.close()
```

---

## 代码格式化

### 行长度

- **最大行长度**: 88 字符 (Ruff 默认)
- **Docstring/注释**: 建议 72 字符

### 空行使用

```python
# 模块级函数之间: 2 个空行
def function_one() -> None:
    pass


def function_two() -> None:
    pass


# 类定义之间: 2 个空行
class ClassOne:
    pass


class ClassTwo:
    pass


# 类内方法之间: 1 个空行
class MyClass:
    def method_one(self) -> None:
        pass

    def method_two(self) -> None:
        pass
```

### 长行处理

```python
# ✅ 正确 - 使用括号隐式续行
result = (
    some_long_function_name(
        argument_one,
        argument_two,
        argument_three,
    )
)

# ✅ 正确 - 方法链
result = (
    df
    .filter(col("status") == "active")
    .groupby("category")
    .agg(sum("amount"))
)

# ❌ 错误 - 使用反斜杠续行
result = some_long_function_name(argument_one, \
    argument_two, argument_three)
```

---

## 检查清单

在 PR Review 时，检查以下代码风格要点：

- [ ] 所有公共接口都有类型提示
- [ ] 没有使用 `Any` 类型
- [ ] 命名符合规范 (snake_case/PascalCase)
- [ ] 公共类和方法都有 Docstring
- [ ] 导入按正确顺序组织
- [ ] 没有通配符导入
- [ ] 异常处理具体而非宽泛
- [ ] 函数复杂度在合理范围内
