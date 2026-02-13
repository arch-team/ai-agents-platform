# 代码风格规范 (Code Style)

> **职责**: Python 代码风格规范，定义类型提示、命名和 Docstring 原则。

---

## 0. 速查卡片

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
| 模块/包 | `snake_case` | `user_repository.py` |

### Docstring 速查

```
类型自解释 → 省略 Docstring | 有副作用/异常 → 说明行为
```

### 异步代码速查

```python
# ✅ 正确 - 并发执行独立任务
results = await asyncio.gather(task1(), task2())

# ✅ 正确 - 上下文管理
async with get_db_session() as session: ...

# ❌ 错误 - 可并行时顺序执行
user = await fetch_user(user_id)
permissions = await fetch_permissions(user_id)
```

### Ruff 自动检查项 (无需人工关注)

导入排序 (isort) | 行长度 120 字符 | 空行规范 | 格式化风格

---

## 1. 类型提示 (Type Hints)

```python
# 泛型类模式
T = TypeVar("T")
class Repository(Generic[T]):
    def get(self, id: int) -> T | None: ...
```

---

## 2. 命名规范

### 命名原则

1. **清晰优于简洁**: `get_user_by_email()` 优于 `get_user()`
2. **动词开头的方法**: `create_user()`, `validate_input()`, `calculate_total()`
3. **布尔值命名**: `is_active`, `has_permission`, `can_edit`
4. **集合命名使用复数**: `users`, `items`, `training_jobs`

---

## 3. Docstring 规范

> **类型即文档**: 类型提示 + 好命名 = 自解释代码。Docstring 只写类型无法表达的内容。

| 场景 | 要求 |
|------|------|
| 类/模块 | ✅ 一句话描述职责 |
| 方法 - 类型自解释 | ❌ 省略 |
| 方法 - 有副作用/异常 | ✅ 说明行为 |
| 私有方法 | ❌ 省略 |

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

## 4. 异步代码规范

```python
# ✅ 正确 - asyncio.gather 并发执行独立任务
user, permissions = await asyncio.gather(
    fetch_user(user_id),
    fetch_permissions(user_id),
)

# ❌ 错误 - 可并行时顺序执行，浪费时间
user = await fetch_user(user_id)
permissions = await fetch_permissions(user_id)

# ❌ 错误 - 在已有事件循环中使用 asyncio.run
def get_user(user_id: int) -> User | None:
    return asyncio.run(self._fetch_user(user_id))  # 禁止
```

---

## 5. 函数签名格式

> **单行优先**: 函数定义（含参数和返回类型）尽量写在一行内，不要将每个参数单独换行。

```python
# ✅ 正确 - 单行签名
async def get_summary(current_user: CurrentUserDep, db: SessionDep) -> DashboardSummaryResponse:

def create_agent(dto: CreateAgentDTO, user_id: int) -> Agent:

async def send_message(conversation_id: int, dto: SendMessageDTO, user_id: int) -> Message:

# ❌ 错误 - 不必要的多行拆分
async def get_summary(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> DashboardSummaryResponse:

# ⚠️ 例外 - 超过 120 字符行宽限制时允许换行，但优先缩短参数名或使用类型别名
async def execute_with_context(
    agent_id: int, conversation_id: int, request: AgentRequest, tools: list[ApprovedToolInfo], gateway_url: str,
) -> AgentResponseChunk:
```

**规则**:
1. 参数 ≤ 120 字符时，**必须**单行
2. 超过 120 字符时，允许换行但尽量紧凑（多参数放同一行直到行宽上限）
3. 禁止"每个参数独占一行"的风格

---

## 6. 导入规范

> 导入分组排序由 Ruff (isort) 自动处理，以下为人工需关注的规则。

- ✅ 具体导入: `from src.domain.entities import User`
- ❌ 通配符导入: `from src.domain.entities import *`
- ✅ 长路径别名: `import sagemaker_client as sagemaker`

---

## 7. 检查清单

完整检查清单见 [checklist.md](checklist.md) §代码风格
