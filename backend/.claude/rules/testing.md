# 测试规范 (Testing Standards)

> **职责**: 测试规范，定义 TDD 工作流、测试分层和 Fixture 模式。

> TDD 工作流见 CLAUDE.md

---

## 0. 速查卡片

### 命令 (CLAUDE.md 补充)

```bash
uv run pytest -m "not slow"           # 排除慢速
uv run pytest --lf                    # 上次失败
uv run pytest tests/modules/auth/     # 指定模块
uv run pytest tests/modules/ -m unit  # 所有模块单元测试
```

### 命名

| 元素 | 模式 | 示例 |
|------|------|------|
| 目录 | `tests/modules/{module}/` | `tests/modules/auth/` |
| 文件 | `test_{component}.py` | `test_user_service.py` |
| 类 | `Test{Class}` | `TestUserService` |
| 方法 | `test_{method}_{scenario}_{expected}` | `test_create_with_invalid_email_raises` |

### 分层

| 层级 | 覆盖 | Mock | 速度 |
|------|------|------|------|
| Unit | Entity/Service | 外部依赖 | ms |
| Integration | API/Repo | 外部服务 | s |
| E2E | 完整流程 | 无 | min |

### 陷阱 ⚠️

- ❌ Mock 被测对象 → ✅ 只 Mock 外部依赖
- ❌ 测试顺序依赖 → ✅ 每测试独立数据
- ❌ 伪造断言 → ✅ 修复代码

### PR 检查

完整检查清单见 [checklist.md](checklist.md) §测试

---

## 1. 目录结构

测试目录**镜像源码模块结构**，确保模块自治和测试可发现性。

```
tests/
├── conftest.py                    # session: 数据库引擎、全局配置
├── factories.py                   # 全局 Factory 定义
├── shared/                        # shared/ 层测试
│   ├── conftest.py
│   ├── domain/
│   │   └── test_base_entity.py
│   └── infrastructure/
│       └── test_pydantic_repository.py
├── modules/                       # 镜像 src/modules/ 结构
│   └── {module}/                  # 每个业务模块
│       ├── conftest.py            # module: Factory/Mock
│       ├── unit/                  # 单元测试 (Domain, Application)
│       │   ├── domain/
│       │   │   ├── test_{entity}_entity.py
│       │   │   └── test_{value_object}.py
│       │   └── application/
│       │       └── test_{entity}_service.py
│       ├── integration/           # 集成测试 (Repository, API)
│       │   ├── test_{entity}_repository.py
│       │   └── test_{module}_endpoints.py
│       └── e2e/                   # 模块内端到端测试
│           └── test_{workflow}.py
└── e2e/                           # 跨模块端到端测试
    ├── conftest.py
    └── test_full_{workflow}.py
```

### Fixture 作用域层级

```
tests/conftest.py                      → session: 数据库引擎、全局配置
tests/modules/{module}/conftest.py     → module: 模块专用 Factory、Mock
tests/modules/{module}/unit/conftest.py → 可选: 单元测试特有 Fixture
```

---

## 2. 测试模式

**AAA 模式** (必须):

```python
def test_create_user_returns_user(self) -> None:
    dto = CreateUserDTO(name="张三", email="a@b.com")  # Arrange
    result = service.create_user(dto)                  # Act
    assert result.name == "张三"                       # Assert
```

**参数化**: `@pytest.mark.parametrize("input,expected", [(val1, exp1), ...])`

**异常**: `with pytest.raises(ValidationError, match="名称不能为空"): ...`

---

## 3. Fixture

| 作用域 | 场景 | 位置 |
|--------|------|------|
| `session` | 数据库引擎 | `tests/conftest.py` |
| `module` | 模块 Factory | `tests/modules/{m}/conftest.py` |
| `function` | 测试数据 | 默认 |

**模式**: `yield` + 清理

```python
@pytest.fixture(scope="session")
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine) -> Session:
    session = sessionmaker(bind=engine)()
    yield session
    session.rollback()
    session.close()
```

---

## 4. Mock

**原则**: 只 Mock 边界 (Repo/外部API/文件系统/时间)

```python
mock_repo = Mock(spec=IUserRepository)
mock_repo.save.return_value = user
service = UserService(repository=mock_repo)
# 验证: mock_repo.save.assert_called_once()
```

**异步**: `AsyncMock(spec=IRepository)`

---

## 5. 标记

```ini
# pytest.ini / pyproject.toml
markers = unit, integration, e2e, slow, aws
```

```python
@pytest.mark.unit
class TestUser: pass

@pytest.mark.integration
@pytest.mark.slow
def test_s3_upload(): pass

@pytest.mark.skip(reason="功能尚未实现")
@pytest.mark.xfail(reason="已知 Bug #123")
```

---

## 6. Factory 模式

```python
# tests/factories.py
class UserFactory(factory.Factory):
    class Meta:
        model = User
    name = factory.Sequence(lambda n: f"用户{n}")
    email = factory.LazyAttribute(lambda o: f"{o.name}@example.com")
```

---

## 7. 覆盖率

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/migrations/*", "*/__init__.py"]

[tool.coverage.report]
fail_under = 85
```

**分层覆盖率目标见 CLAUDE.md**
