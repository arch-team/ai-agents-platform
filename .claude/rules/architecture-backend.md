# 后端架构规范 (Backend Architecture Standards)

> **版本**: 1.2
> **架构模式**: DDD + Modular Monolith + Clean Architecture
> **适用范围**: Python 后端项目

本文档是后端项目的**核心架构规范单一真实源 (Single Source of Truth)**。

---

## 1. 架构概述

### 1.1 技术栈

| 类别 | 技术选型 | 版本要求 |
|------|---------|---------|
| **Web 框架** | FastAPI | 0.110+ |
| **ORM** | SQLAlchemy 2.0 (async) | 2.0+ |
| **数据库** | MySQL 8.0+ (Aurora MySQL 3.x 兼容) | 8.0+ |
| **Python** | Python | 3.11+ |
| **数据验证** | Pydantic | v2 |
| **外部服务** | AWS SageMaker HyperPod | - |

### 1.2 架构模式

本项目采用三层架构模式的融合：

```
┌─────────────────────────────────────────────────────────────┐
│                    DDD (战术设计)                            │
│   Entity, Value Object, Aggregate, Domain Event, Repository │
├─────────────────────────────────────────────────────────────┤
│                 Modular Monolith (模块化)                    │
│   垂直切分业务模块，模块间松耦合，共享基础设施                   │
├─────────────────────────────────────────────────────────────┤
│                 Clean Architecture (分层)                    │
│   依赖倒置，核心业务与外部依赖隔离                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心原则

| 原则 | 说明 | 实践 |
|------|------|------|
| **模块自治** | 每个模块拥有独立的领域模型和业务逻辑 | 模块内 CRUD 完全独立 |
| **显式依赖** | 模块间依赖必须显式声明 | 通过接口定义依赖 |
| **最小知识** | 模块只暴露必要的接口 | 内部实现对外不可见 |
| **单向依赖** | 禁止循环依赖 | 使用事件解耦 |
| **高内聚低耦合** | 相关功能聚合在同一模块 | 按业务领域划分 |

### 1.4 模块划分

| 模块 | 职责 | 核心实体 |
|------|------|---------|
| `auth` | 用户认证与授权 | User |
| `training` | 训练任务管理 | TrainingJob, Checkpoint |
| `quotas` | 资源配额管理 | ResourceQuota, ResourceLimitConfig |
| `models` | 模型管理 | Model |
| `spaces` | 开发空间管理 | Space |
| `audit` | 审计日志 | AuditLog |
| `datasets` | 数据集版本管理与存储 | Dataset, DatasetVersion |
| `billing` | 成本统计与计费分析 | CostRecord, UsageReport |
| `monitoring` | 训练监控与告警 | Metric, Alert |
| `shared` | 共享内核 | BaseEntity, DomainEvent |

---

## 2. 分层规则

### 2.1 模块内部分层

每个业务模块遵循 Clean Architecture 四层结构：

```
┌─────────────────────────────────────────┐
│              API Layer                   │  ← 暴露 HTTP 端点
│         (endpoints, schemas)             │
├─────────────────────────────────────────┤
│          Application Layer               │  ← 业务用例编排
│       (services, dto, interfaces)        │
├─────────────────────────────────────────┤
│            Domain Layer                  │  ← 核心业务逻辑
│  (entities, value_objects, repositories) │
├─────────────────────────────────────────┤
│        Infrastructure Layer              │  ← 技术实现
│     (persistence, external adapters)     │
└─────────────────────────────────────────┘
```

### 2.2 依赖规则 (The Dependency Rule)

| 层级 | 可以依赖 | 禁止依赖 |
|------|---------|---------|
| **Domain** | 无 (纯 Python) | FastAPI, Pydantic, SQLAlchemy, boto3 |
| **Application** | Domain | FastAPI, SQLAlchemy, boto3 |
| **Infrastructure** | Domain, Application | - |
| **API (Presentation)** | Application, Domain (类型) | Infrastructure (通过 DI) |

### 2.2.1 依赖合法性速查矩阵

Claude 生成代码时的快速判断矩阵：

| 从 ↓ 导入 → | `shared/*` | `auth.api.dependencies` | 其他模块 Domain | 其他模块 Service | 其他模块 ORM Model |
|-------------|:----------:|:-----------------------:|:--------------:|:---------------:|:-----------------:|
| **Domain** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Application** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Infrastructure** | ✅ | ❌ | ❌ | ❌ | ⚠️ 仅外键 |
| **API** | ✅ | ✅ | ❌ | ❌ | ❌ |

**图例**: ✅ 允许 | ❌ 禁止 | ⚠️ 条件允许

### 2.3 依赖方向图

```
┌─────────────────────────────────────────────────────────┐
│                    模块内部分层                          │
│                                                         │
│   API 层 ──────────► Application 层 ──────► Domain 层   │
│                           ▲                             │
│                           │                             │
│                    Infrastructure 层                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                    跨模块依赖                            │
│                                                         │
│   modules/A  ───X───►  modules/B   (禁止横向依赖)       │
│       │                    │                            │
│       └────────┬───────────┘                            │
│                ▼                                        │
│           shared/  (唯一允许的共享依赖)                  │
└─────────────────────────────────────────────────────────┘
```

**关键约束**:
- **API 层**: 只能通过 Application Services 执行业务操作；可导入 Domain 层类型用于标注
- **Infrastructure 双重实现**: 同时实现 Domain 层 Repository 接口和 Application 层外部服务接口

---

## 3. 模块间依赖规范

### 3.1 黄金法则

| 规则 | 说明 | 强制性 |
|------|------|--------|
| **R1** | 模块的 Domain 层**绝对不能**导入任何其他模块代码 | 🔴 强制 |
| **R2** | 模块的 Application 层只能依赖**接口**，不能依赖具体实现 | 🔴 强制 |
| **R3** | 模块间通信必须通过**事件总线**或**共享接口** | 🔴 强制 |
| **R4** | `auth` 模块的认证依赖是**唯一例外**，可被其他模块 API 层导入 | 🟡 例外 |

### 3.2 允许的依赖

#### 共享内核依赖

所有模块可以导入 `shared/` 下的内容：

```python
# ✅ Domain 层共享
from src.shared.domain import (
    BaseEntity, PydanticEntity,
    IRepository,
    DomainError, EntityNotFoundError, ValidationError,
    DomainEvent, event_bus, event_handler,
    IQuotaChecker,  # 跨模块接口
)

# ✅ Infrastructure 层共享
from src.shared.infrastructure import get_db, get_settings, PydanticRepository
from src.shared.infrastructure.security import hash_password, verify_password

# ✅ API 层共享
from src.shared.api import domain_exception_handler
from src.shared.api.schemas import EntitySchema, PaginatedResponse
```

**Shared Kernel 约束**:
- `shared/` 只包含技术基础设施和跨模块抽象，**禁止包含任何业务逻辑**
- 跨模块接口 (IQuotaChecker) 只定义契约，实现放在具体模块的 Infrastructure 层

#### Auth 模块特殊依赖（唯一例外）

其他模块的 **API 层** 可以导入 auth 的认证依赖：

```python
# ✅ 仅允许在 API 层导入
from src.modules.auth.api.dependencies import (
    get_current_active_user,
    require_admin,
    require_engineer,
)
from src.modules.auth.api.current_user import CurrentUser
```

### 3.3 禁止的依赖

```python
# ❌ 禁止：直接导入其他模块的服务
from src.modules.training.application.services import TrainingJobService

# ❌ 禁止：直接导入其他模块的实体
from src.modules.quotas.domain.entities import ResourceQuota

# ❌ 禁止：直接导入其他模块的仓库实现
from src.modules.quotas.infrastructure.repositories import QuotaRepositoryImpl

# ❌ 禁止：Domain 层导入任何外部模块
# modules/training/domain/entities/training_job.py
from src.modules.quotas.domain import QuotaError  # 绝对禁止！
```

#### 违规 import 模式检测

Claude 应自动检测并阻止以下 import 模式：

```python
# 违规模式正则表达式 (用于静态检测)
FORBIDDEN_IMPORT_PATTERNS = [
    # 跨模块 Service 导入 (禁止)
    r"from src\.modules\.(?!auth)[\w]+\.application\.services import",
    # 跨模块 Repository 实现导入 (禁止)
    r"from src\.modules\.[\w]+\.infrastructure\.repositories import",
    # 跨模块 Entity 导入 (禁止)
    r"from src\.modules\.(?!auth)[\w]+\.domain\.entities import",
    # Domain 层导入外部框架 (禁止)
    r"# domain/.*\n.*from (fastapi|sqlalchemy|pydantic|boto3) import",
]

# 允许的例外模式
ALLOWED_EXCEPTIONS = [
    # ORM 模型外键关系 (仅 *_model.py 文件)
    r"infrastructure/models/.*_model\.py:.*from src\.modules\.[\w]+\.infrastructure\.models import",
    # Auth 认证依赖 (仅 API 层)
    r"api/.*:.*from src\.modules\.auth\.api\.(dependencies|current_user) import",
]
```

#### 技术例外：ORM 模型外键关系

ORM 模型文件（`*_model.py`）**允许**导入其他模块的 ORM 模型，用于定义外键关系：

```python
# ✅ 允许：ORM 模型定义外键关系
# modules/training/infrastructure/models/training_job_model.py
from src.modules.auth.infrastructure.models import UserModel

class TrainingJobModel(Base):
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="training_jobs")
```

### 3.4 DDD 战术模式规范

#### Entity 实体

**推荐方式 - PydanticEntity (Pydantic V2)**:

```python
from src.shared.domain import PydanticEntity

class User(PydanticEntity):
    """用户实体 - 有唯一身份标识。"""

    username: str = Field(min_length=3, max_length=64)
    email: str
    status: UserStatus = UserStatus.ACTIVE

    def activate(self) -> None:
        """激活用户。"""
        self.status = UserStatus.ACTIVE
        self.touch()  # 更新 updated_at

    def __eq__(self, other: object) -> bool:
        """实体相等性基于 ID。"""
        if not isinstance(other, User):
            return False
        return self.id == other.id
```

**Entity 规范**:
- 继承 `PydanticEntity`，自动获得 `id`, `created_at`, `updated_at`
- 状态转换逻辑在 Entity 内部，**禁止**依赖外部服务或数据库
- 只抛出 Domain 异常，**禁止** `ValueError` 等通用异常

#### Value Object 值对象

```python
import re
from dataclasses import dataclass

from src.shared.domain import ValidationError


@dataclass(frozen=True)  # frozen=True 确保不可变
class Email:
    """邮箱值对象 - 无身份标识，相等性基于值。"""

    value: str

    def __post_init__(self) -> None:
        """初始化后验证。"""
        if not re.match(r"^[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}$", self.value):
            raise ValidationError(f"无效的邮箱格式: {self.value}")

    @property
    def domain(self) -> str:
        return self.value.split("@")[1]
```

#### Repository 仓库

**推荐方式 - PydanticRepository**:

```python
from src.shared.infrastructure import PydanticRepository

class UserRepository(PydanticRepository[User, UserModel, int], IUserRepository):
    """用户仓库实现 - 自动 Entity ↔ Model 转换。"""

    _entity_class = User
    _updatable_fields = ["username", "email", "status", "role"]

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)
```

**Repository 规范**:
- 接口定义在 Domain 层，实现在 Infrastructure 层
- 内置 CRUD：`get_by_id`, `create`, `update`, `delete`, `exists`
- 通过 `_updatable_fields` 控制可更新字段

---

## 4. 模块间通信方式

### 4.1 DDD 集成模式决策矩阵

| 场景 | 推荐模式 | 实现方式 |
|------|---------|---------|
| 实时同步调用 (配额检查) | **Open Host Service** | `shared/domain/interfaces/` |
| 异步通知 (任务完成) | **Published Language** | Domain Events + EventBus |
| 复杂外部系统集成 | **Anti-Corruption Layer** | Infrastructure 适配器 |
| 高度耦合共享概念 | **Shared Kernel** | `shared/domain/` |

### 4.2 事件驱动通信（推荐）

#### 定义域事件

```python
# modules/training/domain/events.py
from dataclasses import dataclass
from src.shared.domain import DomainEvent

@dataclass
class TrainingJobCompletedEvent(DomainEvent):
    """训练任务完成事件。"""
    job_id: int
    owner_id: int
    duration_seconds: int
    final_metrics: dict
```

#### 发布事件

```python
# modules/training/application/services/training_job_service.py
from src.shared.domain import event_bus

class TrainingJobService:
    async def complete_job(self, job_id: int) -> TrainingJob:
        job = await self._repository.get_by_id(job_id)
        job.mark_completed()

        # 发布事件，解耦其他模块
        await event_bus.publish_async(
            TrainingJobCompletedEvent(
                job_id=job.id,
                owner_id=job.owner_id,
                duration_seconds=job.duration,
                final_metrics=job.metrics,
            )
        )
        return await self._repository.update(job)
```

#### 订阅事件

```python
# modules/audit/application/services/audit_service.py
from src.shared.domain import event_handler
from src.modules.training.domain.events import TrainingJobCompletedEvent

class AuditService:
    @event_handler(TrainingJobCompletedEvent)
    async def on_training_completed(self, event: TrainingJobCompletedEvent):
        """监听训练完成，记录审计日志。"""
        await self._create_audit_log(
            entity_type="TrainingJob",
            entity_id=event.job_id,
            action="completed",
        )
```

### 4.3 共享接口通信

当需要同步调用时，通过 `shared/domain/interfaces/` 定义接口：

```python
# shared/domain/interfaces/quota_checker.py
from abc import ABC, abstractmethod

class IQuotaChecker(ABC):
    """配额检查接口 - 供其他模块使用。"""

    @abstractmethod
    async def check_quota(self, user_id: int, resource_type: str, amount: int) -> bool:
        """检查用户配额是否足够。"""
        pass

    @abstractmethod
    async def consume_quota(self, user_id: int, resource_type: str, amount: int) -> None:
        """消费配额。"""
        pass
```

```python
# modules/training/application/services/training_job_service.py
from src.shared.domain.interfaces import IQuotaChecker

class TrainingJobService:
    def __init__(
        self,
        repository: ITrainingJobRepository,
        quota_checker: IQuotaChecker,  # 依赖接口，不依赖实现
    ):
        self._repository = repository
        self._quota_checker = quota_checker

    async def submit_job(self, job: TrainingJob) -> TrainingJob:
        has_quota = await self._quota_checker.check_quota(
            user_id=job.owner_id,
            resource_type="gpu",
            amount=job.gpu_count,
        )
        if not has_quota:
            raise ResourceQuotaExceededError(...)
```

### 4.4 核心域事件清单

| 模块 | 事件 | 触发场景 | 订阅者 |
|------|------|---------|--------|
| **training** | `TrainingJobSubmittedEvent` | 任务提交 | quotas, audit |
| **training** | `TrainingJobCompletedEvent` | 任务完成 | audit, monitoring |
| **training** | `TrainingJobFailedEvent` | 任务失败 | audit, monitoring |
| **quotas** | `QuotaExceededEvent` | 配额超限 | monitoring |
| **auth** | `UserCreatedEvent` | 用户创建 | quotas (初始化配额) |
| **models** | `ModelPublishedEvent` | 模型发布 | audit |

---

## 5. 模块结构规范

### 5.1 目录结构模板

```
modules/{name}/
├── __init__.py             # 模块公开 API 导出
├── api/
│   ├── __init__.py
│   ├── endpoints.py        # FastAPI router
│   ├── dependencies.py     # 依赖注入函数
│   └── schemas/
│       ├── __init__.py
│       ├── requests.py     # 请求模型
│       └── responses.py    # 响应模型
├── application/
│   ├── __init__.py
│   ├── dto/                # 数据传输对象
│   ├── interfaces/         # 端口接口 (外部服务抽象)
│   └── services/
│       ├── __init__.py
│       └── {entity}_service.py
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   └── {entity}.py
│   ├── value_objects/
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── {entity}_repository.py  # 接口
│   ├── events.py
│   └── exceptions.py
└── infrastructure/
    ├── __init__.py
    ├── models/
    │   ├── __init__.py
    │   └── {entity}_model.py   # ORM 模型
    └── repositories/
        ├── __init__.py
        └── {entity}_repository_impl.py
```

### 5.2 文件命名规范

| 类型 | 命名规范 | 示例 |
|------|---------|------|
| 实体 | `{entity}.py` | `training_job.py` |
| 仓库接口 | `{entity}_repository.py` | `training_job_repository.py` |
| 仓库实现 | `{entity}_repository_impl.py` | `training_job_repository_impl.py` |
| ORM 模型 | `{entity}_model.py` | `training_job_model.py` |
| 服务 | `{entity}_service.py` | `training_job_service.py` |

### 5.3 `__init__.py` 导出规则

每个模块必须在 `__init__.py` 明确定义公开 API：

```python
# modules/training/__init__.py
from .api.endpoints import router
from .api.dependencies import get_training_job_service
from .application.services import TrainingJobService
from .domain.entities import TrainingJob, Checkpoint
from .domain.events import TrainingJobCompletedEvent, TrainingJobFailedEvent

__all__ = [
    # API
    "router",
    "get_training_job_service",
    # Application
    "TrainingJobService",
    # Domain
    "TrainingJob",
    "Checkpoint",
    # Events (供其他模块订阅)
    "TrainingJobCompletedEvent",
    "TrainingJobFailedEvent",
]
```

**禁止导出**:
- `TrainingJobModel` (ORM 模型)
- `TrainingJobRepositoryImpl` (仓库实现)
- `HyperPodClient` (外部客户端实现)

---

## 6. 异常处理规范

### 6.1 异常继承体系

```python
# shared/domain/exceptions.py
class DomainError(Exception):
    """域层基础异常。"""
    pass

class EntityNotFoundError(DomainError):
    """实体未找到 - HTTP 404"""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id {entity_id} not found")

class ValidationError(DomainError):
    """验证错误 - HTTP 422"""
    pass

class DuplicateEntityError(DomainError):
    """重复实体 - HTTP 409"""
    pass

class InvalidStateTransitionError(DomainError):
    """无效状态转换 - HTTP 409"""
    pass

class ResourceQuotaExceededError(DomainError):
    """资源配额超限 - HTTP 429"""
    pass
```

### 6.2 HTTP 状态码映射

异常会被 `shared/api/exception_handlers.py` 自动映射：

| 异常类型 | HTTP 状态码 | 场景 |
|---------|-------------|------|
| `EntityNotFoundError` | 404 | 资源不存在 |
| `DuplicateEntityError` | 409 | 资源已存在 |
| `InvalidStateTransitionError` | 409 | 状态转换非法 |
| `ValidationError` | 422 | 参数验证失败 |
| `ResourceQuotaExceededError` | 429 | 配额不足 |

---

## 7. 依赖注入规范

### 7.1 依赖注入层级

```
Layer 1: Database Session (get_db)
    ↓
Layer 2: Repository (get_xxx_repository)
    ↓
Layer 3: External Client (get_xxx_client) - 推荐 Singleton
    ↓
Layer 4: Application Service (get_xxx_service)
    ↓
Layer 5: Permission Check (require_xxx)
```

### 7.2 标准依赖函数模板

```python
# modules/{name}/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure import get_db
from src.modules.{name}.domain.repositories import I{Entity}Repository
from src.modules.{name}.infrastructure.repositories import {Entity}RepositoryImpl
from src.modules.{name}.application.services import {Entity}Service

# Layer 2: Repository
async def get_{entity}_repository(
    session: AsyncSession = Depends(get_db),
) -> I{Entity}Repository:
    return {Entity}RepositoryImpl(session)

# Layer 4: Service
async def get_{entity}_service(
    repository: I{Entity}Repository = Depends(get_{entity}_repository),
) -> {Entity}Service:
    return {Entity}Service(repository=repository)
```

### 7.3 外部客户端 Singleton 模式

```python
# modules/training/infrastructure/hyperpod/client.py
from functools import lru_cache
from src.shared.infrastructure import get_settings

@lru_cache(maxsize=1)
def get_hyperpod_client() -> HyperPodClient:
    """单例模式，避免重复创建 AWS 客户端。"""
    settings = get_settings()
    return HyperPodClient(region=settings.aws_region)
```

### 7.4 跨模块依赖注入

```python
# modules/training/api/dependencies.py
from src.shared.domain.interfaces import IQuotaChecker
from src.modules.quotas.infrastructure import QuotaCheckerImpl

async def get_quota_checker(
    session: AsyncSession = Depends(get_db),
) -> IQuotaChecker:
    quota_repo = ResourceQuotaRepositoryImpl(session)
    return QuotaCheckerImpl(quota_repo)

async def get_training_job_service(
    repository: ITrainingJobRepository = Depends(get_training_job_repository),
    quota_checker: IQuotaChecker = Depends(get_quota_checker),
) -> TrainingJobService:
    return TrainingJobService(
        repository=repository,
        quota_checker=quota_checker,
    )
```

---

## 8. 架构合规检查

### 8.1 自动化测试清单

架构合规测试位于 `tests/unit/test_architecture_compliance.py`：

| 测试类 | 验证规则 |
|--------|---------|
| `TestCleanArchitectureLayers` | 分层依赖方向 |
| `TestModuleDomainLayerIsolation` | R1: Domain 层隔离 |
| `TestModuleApplicationLayerDependencies` | R2: Application 层依赖接口 |
| `TestModuleApiLayerAuthDependency` | R4: Auth 依赖例外 |
| `TestModuleInfrastructureLayerIsolation` | Infrastructure 层隔离 |
| `TestModulePublicApiExports` | 模块 `__all__` 导出 |

### 8.2 运行合规检查

```bash
# 运行所有架构合规测试
pytest tests/unit/test_architecture_compliance.py -v

# 运行特定测试类
pytest tests/unit/test_architecture_compliance.py::TestModuleDomainLayerIsolation -v
```

### 8.3 CI 集成

```yaml
# .github/workflows/ci.yml
- name: Architecture Compliance
  run: |
    pytest tests/unit/test_architecture_compliance.py -v --tb=short
```

---

## 9. 快速参考卡片

### 9.1 依赖速查

```
┌────────────────────────────────────────────────────────┐
│            Modular Monolith 依赖速查                    │
├────────────────────────────────────────────────────────┤
│ ✅ 允许                                                │
│   • 导入 shared/* 任意内容                              │
│   • API 层导入 auth 的认证依赖                          │
│   • 通过 EventBus 发布/订阅事件                         │
│   • 依赖 shared/domain/interfaces 中定义的接口          │
│   • ORM 模型文件导入其他模块 ORM 模型 (外键)            │
├────────────────────────────────────────────────────────┤
│ ❌ 禁止                                                │
│   • Domain 层导入任何外部模块                           │
│   • 直接导入其他模块的 Service                          │
│   • 直接导入其他模块的 Repository 实现                  │
│   • 直接导入其他模块的 Entity                           │
├────────────────────────────────────────────────────────┤
│ 🔄 模块间通信                                          │
│   • 优先: EventBus (异步解耦)                          │
│   • 备选: shared/domain/interfaces (同步调用)          │
│   • 禁止: 直接依赖其他模块实现                          │
└────────────────────────────────────────────────────────┘
```

### 9.2 检查清单

在 PR Review 时，检查以下架构要点：

**分层规则**:
- [ ] Domain 层没有外部框架依赖 (FastAPI, SQLAlchemy, boto3)
- [ ] Application 层只依赖 Domain 层和接口
- [ ] 仓储接口定义在 Domain 层，实现在 Infrastructure 层
- [ ] API 层通过 Application Services 执行业务操作

**模块隔离**:
- [ ] 模块 Domain 层没有导入其他模块
- [ ] 模块间通信使用 EventBus 或 shared/interfaces
- [ ] `__init__.py` 只导出公开 API，不导出实现细节

**DDD 模式**:
- [ ] Entity 使用 PydanticEntity，包含业务逻辑
- [ ] Value Object 使用 frozen dataclass，不可变
- [ ] Repository 接口在 Domain 层，实现在 Infrastructure 层
- [ ] Domain Event 继承自 DomainEvent

**依赖注入**:
- [ ] 依赖注入层级正确 (Session → Repository → Service)
- [ ] 外部服务有对应的接口抽象
- [ ] 跨模块依赖通过 shared/interfaces 注入

---

## 相关文档

| 文档 | 位置 | 说明 |
|------|------|------|
| 主配置 | `.claude/CLAUDE.md` | TDD 工作流、命令、代码风格 |
| 代码风格 | `.claude/rules/code-style.md` | 命名规范、类型提示 |
| 测试规范 | `.claude/rules/testing.md` | TDD 循环、测试分层 |
| 安全规范 | `.claude/rules/security.md` | 安全最佳实践 |
| SDK-First | `.claude/rules/code-standards.md` | SDK 优先原则 |
