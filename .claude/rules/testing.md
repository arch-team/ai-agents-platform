# 测试规范 (Testing Standards)

本文档定义 Python 后端项目的测试规范，采用 TDD (测试驱动开发) 方法论。

---

## 0. 速查卡片 (Quick Reference)

> Claude 生成代码时优先查阅此章节

### 测试命令速查

```bash
# 常用命令
uv run pytest                              # 运行所有测试
uv run pytest -x                           # 遇错停止
uv run pytest --cov=src                    # 带覆盖率
uv run pytest -m "unit"                    # 只跑单元测试
uv run pytest -m "not slow"                # 排除慢速测试
uv run pytest tests/unit/test_user.py -v  # 指定文件，详细输出
```

### TDD 循环速查

```
🔴 Red    → 先写失败测试，明确预期行为
🟢 Green  → 最少代码使测试通过，不过度设计
🔄 Refactor → 重构代码，保持测试通过
```

### 命名模式速查

| 元素 | 模式 | 示例 |
|------|------|------|
| 文件 | `test_<模块>.py` | `test_user_service.py` |
| 类 | `Test<被测类>` | `TestUserService` |
| 方法 | `test_<方法>_<场景>_<预期>` | `test_create_user_with_invalid_email_raises_error` |

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
- [ ] 测试遵循 AAA 模式 (Arrange-Act-Assert)
- [ ] 测试命名清晰描述测试目的
- [ ] Mock 只用于外部依赖
- [ ] 测试可独立运行，无顺序依赖
- [ ] 使用了合适的测试标记 (`@pytest.mark.unit` 等)

---

## 1. 测试结构

### 目录组织

```
tests/
├── conftest.py           # 全局 Fixture
├── unit/                 # 单元测试 (Domain, Application)
│   ├── conftest.py
│   ├── domain/
│   └── application/
├── integration/          # 集成测试 (API, Repository)
│   ├── conftest.py
│   ├── api/
│   └── repositories/
└── e2e/                  # 端到端测试
    └── conftest.py
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
# tests/conftest.py

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

@pytest.fixture
def user_factory(db_session: Session):
    """用户工厂 Fixture。"""
    def _create(name: str = "测试用户", email: str = "test@example.com"):
        user = User(name=name, email=Email(email))
        db_session.add(user)
        db_session.commit()
        return user
    return _create
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
