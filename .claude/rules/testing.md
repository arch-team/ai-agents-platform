# 测试规范 (Testing Standards)

本文档定义 Python 后端项目的测试规范，采用 TDD (测试驱动开发) 方法论。

---

## 0. 速查卡片 (Quick Reference)

> Claude 生成代码时优先查阅此章节

### 测试命令 & TDD 循环

**见 CLAUDE.md**: "## 开发命令 > ### 测试" (完整命令) | "### TDD 工作流" (核心循环)

```bash
# 本文件补充命令 (CLAUDE.md 未包含)
uv run pytest -m "not slow"                # 排除慢速测试
uv run pytest --tb=short                   # 简洁错误输出
uv run pytest --lf                         # 只跑上次失败的测试

# 模块化测试命令 (推荐)
uv run pytest tests/modules/auth/          # auth 模块所有测试
uv run pytest tests/modules/auth/unit/     # auth 模块单元测试
uv run pytest tests/modules/ -m unit       # 所有模块单元测试
uv run pytest tests/modules/ -m integration # 所有模块集成测试
uv run pytest tests/e2e/                   # 跨模块端到端测试
```

### 命名模式速查

| 元素 | 模式 | 示例 |
|------|------|------|
| 测试目录 | `tests/modules/{module}/` | `tests/modules/auth/` |
| 测试文件 | `test_{component}.py` | `test_user_service.py` |
| 测试类 | `Test{被测类}` | `TestUserService` |
| 测试方法 | `test_{方法}_{场景}_{预期}` | `test_create_user_with_invalid_email_raises_error` |

### 常见陷阱 ⚠️

| 陷阱 | ❌ 错误 | ✅ 正确 |
|------|--------|--------|
| Mock 被测对象 | `mocker.patch.object(UserService, 'create_user')` | 只 mock 外部依赖 |
| 测试顺序依赖 | 测试 A 创建数据，测试 B 依赖该数据 | 每个测试独立创建数据 |
| 过度 Mock | Mock 所有依赖 | 只 Mock 外部服务/IO |
| 伪造测试结果 | 修改断言使测试通过 | 修复代码使测试通过 |
| 缺少边界测试 | 只测试正常路径 | 测试边界条件和异常 |

### PR Review 检查清单

- [ ] 新功能有对应测试
- [ ] 测试文件放在正确的模块目录 (`tests/modules/{module}/`)
- [ ] 测试遵循 AAA 模式 (Arrange-Act-Assert)
- [ ] 测试命名清晰描述测试目的
- [ ] Mock 只用于外部依赖
- [ ] 测试可独立运行，无顺序依赖
- [ ] 使用了合适的测试标记 (`@pytest.mark.unit` 等)

---

## 1. 测试结构

### 目录组织

测试目录**镜像源码模块结构**，确保模块自治和测试可发现性。

```
tests/
├── conftest.py                    # 全局 Fixture (数据库引擎、通用工具)
├── factories.py                   # 全局 Factory 定义
├── shared/                        # shared/ 层测试
│   ├── conftest.py
│   ├── domain/
│   │   └── test_base_entity.py
│   └── infrastructure/
│       └── test_pydantic_repository.py
├── modules/                       # 镜像 src/modules/ 结构
│   ├── {module}/                  # 每个业务模块
│   │   ├── conftest.py            # 模块级 Fixture
│   │   ├── unit/                  # 单元测试 (Domain, Application)
│   │   │   ├── domain/
│   │   │   │   ├── test_{entity}_entity.py
│   │   │   │   └── test_{value_object}.py
│   │   │   └── application/
│   │   │       └── test_{entity}_service.py
│   │   ├── integration/           # 集成测试 (Repository, API)
│   │   │   ├── test_{entity}_repository.py
│   │   │   └── test_{module}_endpoints.py
│   │   └── e2e/                   # 模块内端到端测试
│   │       └── test_{workflow}.py
│   ├── auth/                      # 示例: auth 模块
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── domain/
│   │   │   │   └── test_user_entity.py
│   │   │   └── application/
│   │   │       └── test_user_service.py
│   │   └── integration/
│   │       └── test_auth_endpoints.py
│   └── training/                  # 示例: training 模块
│       └── ...
└── e2e/                           # 跨模块端到端测试
    ├── conftest.py
    └── test_full_{workflow}.py
```

### 测试目录命名规则

| 位置 | 命名规则 | 示例 |
|------|---------|------|
| 模块测试根目录 | `tests/modules/{module}/` | `tests/modules/auth/` |
| 单元测试 | `unit/{layer}/test_{component}.py` | `unit/domain/test_user_entity.py` |
| 集成测试 | `integration/test_{target}.py` | `integration/test_user_repository.py` |
| 模块 E2E | `e2e/test_{workflow}.py` | `e2e/test_login_flow.py` |
| 跨模块 E2E | `tests/e2e/test_{workflow}.py` | `tests/e2e/test_training_workflow.py` |

### Fixture 作用域层级

```
tests/conftest.py                      → session 级: 数据库引擎、全局配置
tests/modules/{module}/conftest.py     → module 级: 模块专用 Factory、Mock
tests/modules/{module}/unit/conftest.py → 可选: 单元测试特有 Fixture
```

### 测试分层策略

| 层级 | 覆盖范围 | Mock 策略 | 速度 |
|------|---------|----------|------|
| **Unit** | Entity, ValueObject, DomainService, ApplicationService | Mock 所有外部依赖 | 毫秒级 |
| **Integration** | API 端点, Repository 实现, 外部适配器 | Mock 外部服务，真实数据库 | 秒级 |
| **E2E** | 完整业务流程, AWS 服务集成 | 无 Mock，真实环境 | 分钟级 |

---

## 2. 测试模式

### AAA 模式 (必须遵循)

```python
def test_create_user_with_valid_email_returns_user(self) -> None:
    # Arrange - 准备测试数据
    dto = CreateUserDTO(name="张三", email="test@example.com")

    # Act - 执行被测操作
    result = service.create_user(dto)

    # Assert - 验证结果
    assert result.name == "张三"
    assert result.email.value == "test@example.com"
```

### 参数化测试

```python
@pytest.mark.parametrize("email,expected_valid", [
    ("user@example.com", True),
    ("invalid", False),
    ("@example.com", False),
])
def test_email_validation(self, email: str, expected_valid: bool) -> None:
    if expected_valid:
        assert Email(email).value == email
    else:
        with pytest.raises(ValidationError):
            Email(email)
```

### 异常测试

```python
def test_create_user_with_empty_name_raises_error(self) -> None:
    with pytest.raises(ValidationError, match="名称不能为空"):
        User(name="", email=Email("test@example.com"))
```

---

## 3. Fixture 规范

### 作用域选择

| 作用域 | 使用场景 | 示例 |
|--------|---------|------|
| `function` | 每个测试独立数据 (默认) | 用户实体、DTO |
| `class` | 同一测试类共享 | 测试客户端 |
| `module` | 同一模块共享 | 数据库连接 |
| `session` | 整个测试会话共享 | 数据库引擎 |

### 常用 Fixture 模式

```python
# tests/conftest.py (全局 Fixture)

@pytest.fixture(scope="session")
def engine():
    """数据库引擎 (会话级)。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine) -> Session:
    """数据库会话 (函数级)，自动回滚。"""
    session = sessionmaker(bind=engine)()
    yield session
    session.rollback()
    session.close()
```

```python
# tests/modules/auth/conftest.py (模块级 Fixture)

@pytest.fixture
def user_factory(db_session: Session):
    """用户工厂 Fixture - auth 模块专用。"""
    def _create(name: str = "测试用户", email: str = "test@example.com"):
        user = User(name=name, email=Email(email))
        db_session.add(user)
        db_session.commit()
        return user
    return _create

@pytest.fixture
def mock_auth_service() -> Mock:
    """Mock 认证服务 - auth 模块测试专用。"""
    return Mock(spec=IAuthService)
```

---

## 4. Mock 规范

### Mock 原则

| 原则 | 说明 |
|------|------|
| **只 Mock 边界** | Repository, 外部 API, 文件系统, 时间 |
| **不 Mock 被测对象** | 被测类的方法不应被 Mock |
| **验证交互** | 使用 `assert_called_once_with()` 验证参数 |

### Mock 示例

```python
class TestUserService:
    @pytest.fixture
    def mock_repo(self) -> Mock:
        return Mock(spec=IUserRepository)

    @pytest.fixture
    def service(self, mock_repo: Mock) -> UserService:
        return UserService(repository=mock_repo)

    def test_create_user_saves_to_repository(
        self, service: UserService, mock_repo: Mock
    ) -> None:
        dto = CreateUserDTO(name="张三", email="test@example.com")
        mock_repo.save.return_value = User(name="张三", email=Email("test@example.com"))

        result = service.create_user(dto)

        mock_repo.save.assert_called_once()
        assert result.name == "张三"
```

### AsyncMock 用于异步方法

```python
@pytest.fixture
def mock_async_repo() -> AsyncMock:
    repo = AsyncMock(spec=IUserRepository)
    repo.get_by_id.return_value = User(...)
    return repo
```

---

## 5. 测试标记

### 标记定义 (pytest.ini)

```ini
[pytest]
markers =
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
    slow: 耗时测试 (>1s)
    aws: 需要 AWS 服务
```

### 使用示例

```python
@pytest.mark.unit
class TestUser:
    """用户实体单元测试。"""
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_s3_upload() -> None:
    """S3 上传集成测试。"""
    pass

@pytest.mark.skip(reason="功能尚未实现")
def test_future_feature() -> None:
    pass

@pytest.mark.xfail(reason="已知 Bug #123")
def test_known_issue() -> None:
    pass
```

---

## 6. 测试数据管理

### 数据原则

| 原则 | 说明 |
|------|------|
| **测试隔离** | 每个测试使用独立数据，不依赖其他测试 |
| **最小数据** | 只创建测试需要的数据 |
| **可重复** | 测试可以多次运行，结果一致 |
| **自动清理** | 使用 Fixture 自动清理，不留残留数据 |

### Factory 模式

```python
# tests/factories.py
import factory
from src.domain.entities import User, TrainingJob

class UserFactory(factory.Factory):
    class Meta:
        model = User

    name = factory.Sequence(lambda n: f"用户{n}")
    email = factory.LazyAttribute(lambda o: f"{o.name}@example.com")
    is_active = True

class TrainingJobFactory(factory.Factory):
    class Meta:
        model = TrainingJob

    name = factory.Sequence(lambda n: f"训练任务{n}")
    status = "PENDING"
```

---

## 7. 覆盖率配置

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/migrations/*", "*/__init__.py", "*/conftest.py"]

[tool.coverage.report]
fail_under = 85
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

**分层覆盖率目标见 CLAUDE.md**
