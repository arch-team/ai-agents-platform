# 测试规范 (Testing Standards)

本文档定义 Python 后端项目的测试规范，采用 TDD (测试驱动开发) 方法论。

---

## TDD 工作流

### 核心循环

```
1. 🔴 Red: 先写失败的测试
   - 明确定义预期行为
   - 运行测试，确认失败

2. 🟢 Green: 编写最少代码使测试通过
   - 只写满足测试的代码
   - 不过度设计

3. 🔄 Refactor: 重构代码，保持测试通过
   - 消除重复
   - 改善代码结构
   - 确保测试仍然通过
```

### TDD 原则

| 原则 | 说明 |
|------|------|
| **测试先行** | 永远先写测试，再写实现 |
| **小步前进** | 每次只实现一个小功能 |
| **测试诚信** | 切勿为让测试通过而伪造结果 |
| **快速反馈** | 测试应该快速运行 |

---

## 测试结构

### 目录组织

```
tests/
├── __init__.py
├── conftest.py           # 全局共享 Fixture
├── unit/                 # 单元测试
│   ├── __init__.py
│   ├── conftest.py       # 单元测试 Fixture
│   ├── domain/           # 领域层测试
│   │   ├── test_user.py
│   │   └── test_training_job.py
│   └── application/      # 应用层测试
│       ├── test_user_service.py
│       └── test_job_service.py
├── integration/          # 集成测试
│   ├── __init__.py
│   ├── conftest.py       # 集成测试 Fixture
│   ├── api/              # API 端点测试
│   │   ├── test_user_api.py
│   │   └── test_job_api.py
│   └── repositories/     # 仓储实现测试
│       └── test_user_repository.py
└── e2e/                  # 端到端测试
    ├── __init__.py
    ├── conftest.py
    └── test_training_workflow.py
```

### 测试文件命名

```python
# 测试文件: test_<模块名>.py
test_user_service.py
test_training_job_repository.py

# 测试类: Test<被测类名>
class TestUserService:
    pass

class TestTrainingJobRepository:
    pass
```

---

## 测试命名规范

### 命名模式

```python
def test_<方法名>_<场景描述>_<预期结果>():
    pass
```

### 命名示例

```python
class TestUserService:
    """用户服务测试类。"""

    def test_create_user_with_valid_email_returns_user(self) -> None:
        """测试使用有效邮箱创建用户返回用户实体。"""
        pass

    def test_create_user_with_invalid_email_raises_validation_error(self) -> None:
        """测试使用无效邮箱创建用户抛出验证错误。"""
        pass

    def test_create_user_with_duplicate_email_raises_duplicate_error(self) -> None:
        """测试使用已存在邮箱创建用户抛出重复错误。"""
        pass

    def test_get_user_with_existing_id_returns_user(self) -> None:
        """测试使用存在的 ID 获取用户返回用户实体。"""
        pass

    def test_get_user_with_nonexistent_id_returns_none(self) -> None:
        """测试使用不存在的 ID 获取用户返回 None。"""
        pass
```

---

## 测试分层策略

### 单元测试 (Unit Tests)

**目标**: 测试单个组件的隔离行为

**覆盖范围**:
- 领域实体和值对象
- 领域服务
- 应用层用例
- 工具函数

```python
# tests/unit/domain/test_user.py

import pytest
from src.domain.entities import User
from src.domain.value_objects import Email
from src.domain.exceptions import ValidationError


class TestUser:
    """用户实体单元测试。"""

    def test_create_user_with_valid_data_succeeds(self) -> None:
        """测试使用有效数据创建用户成功。"""
        # Arrange
        name = "张三"
        email = Email("zhangsan@example.com")

        # Act
        user = User(name=name, email=email)

        # Assert
        assert user.name == name
        assert user.email == email
        assert user.is_active is True

    def test_create_user_with_empty_name_raises_error(self) -> None:
        """测试使用空名称创建用户抛出错误。"""
        # Arrange
        email = Email("zhangsan@example.com")

        # Act & Assert
        with pytest.raises(ValidationError, match="名称不能为空"):
            User(name="", email=email)


class TestEmail:
    """邮箱值对象单元测试。"""

    @pytest.mark.parametrize(
        "email",
        [
            "user@example.com",
            "user.name@example.co.jp",
            "user+tag@example.org",
        ],
    )
    def test_create_email_with_valid_format_succeeds(self, email: str) -> None:
        """测试使用有效格式创建邮箱成功。"""
        result = Email(email)
        assert str(result) == email

    @pytest.mark.parametrize(
        "email",
        [
            "invalid",
            "@example.com",
            "user@",
            "user @example.com",
        ],
    )
    def test_create_email_with_invalid_format_raises_error(self, email: str) -> None:
        """测试使用无效格式创建邮箱抛出错误。"""
        with pytest.raises(ValidationError):
            Email(email)
```

### 集成测试 (Integration Tests)

**目标**: 测试组件之间的交互

**覆盖范围**:
- API 端点
- 仓储实现
- 外部服务适配器

```python
# tests/integration/api/test_user_api.py

import pytest
from fastapi.testclient import TestClient
from src.presentation.api.main import app


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端。"""
    return TestClient(app)


class TestUserAPI:
    """用户 API 集成测试。"""

    def test_create_user_returns_201(self, client: TestClient) -> None:
        """测试创建用户返回 201 状态码。"""
        # Arrange
        payload = {
            "name": "张三",
            "email": "zhangsan@example.com"
        }

        # Act
        response = client.post("/api/v1/users", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "张三"
        assert data["email"] == "zhangsan@example.com"
        assert "id" in data

    def test_create_user_with_invalid_email_returns_422(
        self, client: TestClient
    ) -> None:
        """测试使用无效邮箱创建用户返回 422 状态码。"""
        # Arrange
        payload = {
            "name": "张三",
            "email": "invalid-email"
        }

        # Act
        response = client.post("/api/v1/users", json=payload)

        # Assert
        assert response.status_code == 422

    def test_get_user_returns_200(
        self, client: TestClient, created_user: dict
    ) -> None:
        """测试获取用户返回 200 状态码。"""
        # Arrange
        user_id = created_user["id"]

        # Act
        response = client.get(f"/api/v1/users/{user_id}")

        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == user_id
```

### 端到端测试 (E2E Tests)

**目标**: 测试完整的用户流程

**覆盖范围**:
- 关键业务流程
- 系统边界测试
- AWS 服务集成

```python
# tests/e2e/test_training_workflow.py

import pytest
from tests.e2e.conftest import E2ETestClient


@pytest.mark.e2e
class TestTrainingWorkflow:
    """训练工作流端到端测试。"""

    @pytest.mark.slow
    def test_complete_training_workflow(self, e2e_client: E2ETestClient) -> None:
        """测试完整的训练工作流。"""
        # 1. 创建训练任务
        job = e2e_client.create_training_job(
            model_name="llama-7b",
            dataset_s3_uri="s3://bucket/data",
            instance_type="ml.p4d.24xlarge",
        )
        assert job["status"] == "PENDING"

        # 2. 等待任务开始
        e2e_client.wait_for_status(job["id"], "RUNNING", timeout=300)

        # 3. 验证日志输出
        logs = e2e_client.get_job_logs(job["id"])
        assert "Training started" in logs

        # 4. 等待任务完成
        e2e_client.wait_for_status(job["id"], "COMPLETED", timeout=3600)

        # 5. 验证输出
        result = e2e_client.get_job_result(job["id"])
        assert result["model_s3_uri"] is not None
        assert result["metrics"]["loss"] < 1.0
```

---

## Fixture 规范

### 共享 Fixture

```python
# tests/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.database import Base


@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎 (会话级别)。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine) -> Session:
    """创建数据库会话 (函数级别)。"""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def user_factory(db_session: Session):
    """用户工厂 Fixture。"""
    def _create_user(name: str = "测试用户", email: str = "test@example.com"):
        from src.domain.entities import User
        from src.domain.value_objects import Email
        user = User(name=name, email=Email(email))
        db_session.add(user)
        db_session.commit()
        return user
    return _create_user
```

### Fixture 作用域

| 作用域 | 使用场景 |
|--------|---------|
| `function` | 每个测试函数独立数据 (默认) |
| `class` | 同一测试类共享数据 |
| `module` | 同一模块共享数据 |
| `session` | 整个测试会话共享数据 |

---

## Mock 和 Stub 规范

### 使用 pytest-mock

```python
# tests/unit/application/test_user_service.py

import pytest
from unittest.mock import AsyncMock, Mock

from src.application.services import UserService
from src.domain.entities import User
from src.domain.value_objects import Email


class TestUserService:
    """用户服务测试。"""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """模拟仓储。"""
        return Mock()

    @pytest.fixture
    def mock_email_service(self) -> Mock:
        """模拟邮件服务。"""
        return Mock()

    @pytest.fixture
    def user_service(
        self, mock_repository: Mock, mock_email_service: Mock
    ) -> UserService:
        """创建用户服务实例。"""
        return UserService(
            repository=mock_repository,
            email_service=mock_email_service,
        )

    def test_create_user_saves_to_repository(
        self,
        user_service: UserService,
        mock_repository: Mock,
    ) -> None:
        """测试创建用户时保存到仓储。"""
        # Arrange
        dto = CreateUserDTO(name="张三", email="zhangsan@example.com")
        expected_user = User(name="张三", email=Email("zhangsan@example.com"))
        mock_repository.save.return_value = expected_user

        # Act
        result = user_service.create_user(dto)

        # Assert
        mock_repository.save.assert_called_once()
        assert result.name == "张三"

    def test_create_user_sends_welcome_email(
        self,
        user_service: UserService,
        mock_repository: Mock,
        mock_email_service: Mock,
    ) -> None:
        """测试创建用户时发送欢迎邮件。"""
        # Arrange
        dto = CreateUserDTO(name="张三", email="zhangsan@example.com")
        mock_repository.save.return_value = User(
            name="张三", email=Email("zhangsan@example.com")
        )

        # Act
        user_service.create_user(dto)

        # Assert
        mock_email_service.send_welcome_email.assert_called_once_with(
            "zhangsan@example.com"
        )
```

### Mock 最佳实践

```python
# ✅ 正确 - 只 mock 外部依赖
def test_user_service(mock_repository: Mock) -> None:
    service = UserService(repository=mock_repository)
    ...

# ❌ 错误 - mock 被测试的对象本身
def test_user_service(mocker) -> None:
    mocker.patch.object(UserService, 'create_user')  # 不应该 mock 被测方法
    ...

# ✅ 正确 - 验证交互
mock_repository.save.assert_called_once_with(expected_user)

# ❌ 错误 - 过度验证
mock_repository.save.assert_called_once()  # 没有验证参数
```

---

## 测试标记

### 常用标记

```python
import pytest

@pytest.mark.unit
def test_unit_example() -> None:
    """单元测试示例。"""
    pass

@pytest.mark.integration
def test_integration_example() -> None:
    """集成测试示例。"""
    pass

@pytest.mark.e2e
def test_e2e_example() -> None:
    """端到端测试示例。"""
    pass

@pytest.mark.slow
def test_slow_example() -> None:
    """耗时测试示例。"""
    pass

@pytest.mark.skip(reason="功能尚未实现")
def test_skip_example() -> None:
    """跳过的测试示例。"""
    pass

@pytest.mark.xfail(reason="已知问题，等待修复")
def test_xfail_example() -> None:
    """预期失败的测试示例。"""
    pass
```

### pytest.ini 标记配置

```ini
[pytest]
markers =
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
    slow: 耗时测试
    aws: 需要 AWS 服务的测试
```

---

## 覆盖率要求

### 覆盖率配置

```ini
# pyproject.toml 中的 coverage 配置
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/migrations/*",
    "*/__init__.py",
    "*/conftest.py",
]

[tool.coverage.report]
fail_under = 85
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### 分层覆盖率目标

| 层级 | 最低覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| Domain | 95% | 100% |
| Application | 90% | 95% |
| Infrastructure | 80% | 85% |
| Presentation | 80% | 85% |
| **整体** | **85%** | **90%** |

---

## 测试数据管理

### 测试数据原则

1. **测试隔离**: 每个测试使用独立数据
2. **最小数据**: 只创建测试需要的数据
3. **可重复**: 测试可以重复运行
4. **清理**: 测试后清理创建的数据

### 测试数据工厂

```python
# tests/factories.py

from dataclasses import dataclass
from typing import Any
import factory
from src.domain.entities import User, TrainingJob


class UserFactory(factory.Factory):
    """用户工厂。"""

    class Meta:
        model = User

    name = factory.Sequence(lambda n: f"用户{n}")
    email = factory.LazyAttribute(
        lambda obj: f"{obj.name.lower()}@example.com"
    )
    is_active = True


class TrainingJobFactory(factory.Factory):
    """训练任务工厂。"""

    class Meta:
        model = TrainingJob

    name = factory.Sequence(lambda n: f"训练任务{n}")
    model_name = "llama-7b"
    instance_type = "ml.p4d.24xlarge"
    status = "PENDING"
```

---

## 检查清单

在 PR Review 时，检查以下测试要点：

- [ ] 所有新功能都有对应的测试
- [ ] 测试遵循 AAA 模式 (Arrange-Act-Assert)
- [ ] 测试命名清晰描述了测试目的
- [ ] 使用了合适的测试标记
- [ ] Mock 只用于外部依赖
- [ ] 测试覆盖率达到要求
- [ ] 测试可以独立运行
- [ ] 没有测试依赖于执行顺序
