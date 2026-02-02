# AI 训练平台后端架构规范

> **版本**: 1.1
> **最后更新**: 2026-01-26
> **架构模式**: DDD + Modular Monolith + Clean Architecture

本文档是后端项目的**核心架构规范单一真实源 (Single Source of Truth)**。所有架构相关决策应以本文档为准。

---

## 目录

1. [架构概述](#1-架构概述)
2. [分层规则](#2-分层规则)
3. [模块间依赖规范](#3-模块间依赖规范)
4. [模块间通信方式](#4-模块间通信方式)
5. [模块结构规范](#5-模块结构规范)
6. [异常处理规范](#6-异常处理规范)
7. [依赖注入规范](#7-依赖注入规范)
8. [架构合规检查](#8-架构合规检查)
9. [附录](#9-附录)

---

## 1. 架构概述

### 1.1 技术栈

| 类别 | 技术选型 |
|------|---------|
| **Web 框架** | FastAPI 0.100+ |
| **ORM** | SQLAlchemy 2.0 (async) |
| **数据库** | MySQL 8.0+ (Aurora MySQL 3.x 兼容) |
| **Python** | 3.11+ |
| **外部服务** | AWS SageMaker HyperPod |

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
│   依赖倒置，核心业务与外部依赖隔离                                │
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

```
modules/{name}/
├── api/                    # API 层 (入口适配器)
│   ├── endpoints.py        # REST 端点定义
│   ├── schemas/            # Pydantic 请求/响应模型
│   └── dependencies.py     # FastAPI 依赖注入
├── application/            # 应用层 (业务用例编排，协调领域对象和基础设施)
│   └── dto/                # 数据传输对象 (跨层传输)
│   └── services/           # 业务用例实现
│   └── interfaces/         # 端口接口 (外部服务抽象，定义 Application 层需要的外部能力接口)
├── domain/                 # 领域层 (核心业务逻辑)
│   ├── entities/           # 领域实体
│   ├── value_objects/      # 值对象
│   ├── repositories/       # 仓库接口 (抽象)
│   ├── events.py           # 领域事件定义
│   └── exceptions.py       # 领域异常
└── infrastructure/         # 基础设施层 (外部适配器)
    ├── models/             # ORM 模型
    ├── repositories/       # 仓库实现
    └── {external}/         # 外部服务客户端
```

### 2.2 依赖方向

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

**关键规则**:
- 依赖只能从外层指向内层
- Domain 层是最内层，不依赖任何外部
- Infrastructure 层实现 Domain 层定义的接口
- **API 层约束**:
  - API 层只能通过 Application Services 执行业务操作（创建、修改、删除）
  - API 层可以导入 Domain 层的类型定义（实体类、值对象、枚举）用于类型标注和响应映射
  - API 层禁止直接访问 Infrastructure 实现
- **Infrastructure 双重实现**: Infrastructure 层同时实现 Domain 层的 Repository 接口和 Application 层的外部服务接口 (interfaces/)

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

#### 3.2.1 共享内核依赖

所有模块可以导入 `shared/` 下的内容：

```python
# ✅ Domain 层共享
from src.shared.domain import (
    BaseEntity,
    IRepository,
    DomainError,
    EntityNotFoundError,
    ValidationError,
    DuplicateEntityError,
    InvalidStateTransitionError,
    ResourceQuotaExceededError,
    DomainEvent,
    event_bus,
    event_handler,
    IQuotaChecker,  # 跨模块接口
)

# ✅ Infrastructure 层共享
from src.shared.infrastructure import get_db, get_settings
from src.shared.infrastructure.security import hash_password, verify_password

# ✅ API 层共享
from src.shared.api import domain_exception_handler
from src.shared.api.schemas import EntitySchema, PaginatedResponse

# ✅ 工具共享
from src.shared.utils import utc_now, paginate
```

**Shared Kernel 约束**:
- `shared/` 只包含技术基础设施和跨模块抽象，**禁止包含任何业务逻辑**
- Domain 类型 (BaseEntity, DomainEvent) 是纯技术抽象，不包含业务规则
- 跨模块接口 (IQuotaChecker) 只定义契约，实现放在具体模块的 Infrastructure 层

#### 3.2.2 Auth 模块特殊依赖（唯一例外）

其他模块的 **API 层** 可以导入 auth 的认证依赖：

```python
# ✅ 仅允许在 API 层导入
from src.modules.auth.api.dependencies import (
    get_current_active_user,
    require_admin,
    require_engineer,
    require_viewer,
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
from src.modules.quotas.infrastructure.repositories import ModelRepositoryImpl

# ❌ 禁止：Domain 层导入任何外部模块
# modules/training/domain/entities/training_job.py
from src.modules.quotas.domain import QuotaError  # 绝对禁止！
```

#### 3.3.1 技术例外：ORM 模型外键关系

ORM 模型文件（`*_model.py`）**允许**导入其他模块的 ORM 模型，用于定义 SQLAlchemy 外键关系：

```python
# ✅ 允许：ORM 模型定义外键关系
# modules/training/infrastructure/models/training_job_model.py
from src.modules.auth.infrastructure.models import UserModel  # FK to users

class TrainingJobModel(Base):
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="training_jobs")
```

**原因**: SQLAlchemy 要求在定义外键关系时引用目标模型类，这是数据库关系映射的技术必要性。

**约束**: 此例外仅限于 ORM 模型文件（`*_model.py`），其他基础设施代码（如仓库实现）仍需遵循模块隔离原则。

### 3.4 DDD 战术模式规范

#### Entity 实体

**推荐方式 - PydanticEntity（Pydantic V2）**:
```python
from src.shared.domain import PydanticEntity

class User(PydanticEntity):
    username: str = Field(min_length=3, max_length=64)
    email: str
    status: UserStatus = UserStatus.ACTIVE

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE
        self.touch()  # 更新 updated_at
```

特性：
- 继承 `PydanticEntity`，自动获得 ORM 转换能力 (`from_attributes=True`)
- 内置字段：`id`, `created_at`, `updated_at`
- 使用 `touch()` 更新时间戳
- 状态转换逻辑在 Entity 内部，**禁止**依赖外部服务或数据库
- 只抛出 Domain 异常，**禁止** `ValueError` 等通用异常

**旧方式 - BaseEntity（dataclass）**: 仅用于特殊场景，新代码应使用 `PydanticEntity`

#### Value Object 值对象
- 使用 `@dataclass(frozen=True)` 确保不可变，相等性基于值比较
- 在 `__post_init__` 验证，无效值抛出 `ValidationError`

#### Repository 仓库

**推荐方式 - PydanticRepository**:
```python
from src.shared.infrastructure import PydanticRepository

class UserRepository(PydanticRepository[User, UserModel, int], IUserRepository):
    _entity_class = User
    _updatable_fields = ["username", "email", "status", "role"]

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)
```

特性：
- 自动 Entity ↔ Model 转换，无需手写 `_to_entity()`, `_to_model()`
- 内置 CRUD：`get_by_id`, `create`, `update`, `delete`, `exists`
- 通过 `_updatable_fields` 控制可更新字段
- 支持软删除、分页查询

**旧方式 - BaseRepository**: 仅用于复杂转换场景（如 `UploadSession`）

#### Domain Event 域事件
- 继承 `DomainEvent`，自动含 `event_id: UUID` 和 `occurred_at: datetime`

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
    """训练任务完成事件"""
    job_id: int
    owner_id: int
    duration_seconds: int
    final_metrics: dict

@dataclass
class TrainingJobFailedEvent(DomainEvent):
    """训练任务失败事件"""
    job_id: int
    owner_id: int
    error_message: str
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
        """监听训练完成，记录审计日志"""
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
    """配额检查接口 - 供其他模块使用"""

    @abstractmethod
    async def check_quota(
        self, user_id: int, resource_type: str, amount: int
    ) -> bool:
        """检查用户配额是否足够"""
        pass

    @abstractmethod
    async def consume_quota(
        self, user_id: int, resource_type: str, amount: int
    ) -> None:
        """消费配额"""
        pass

    @abstractmethod
    async def release_quota(
        self, user_id: int, resource_type: str, amount: int
    ) -> None:
        """释放配额"""
        pass
```

```python
# modules/quotas/infrastructure/quota_checker_impl.py
from src.shared.domain.interfaces import IQuotaChecker

class QuotaCheckerImpl(IQuotaChecker):
    def __init__(self, quota_repository: IResourceQuotaRepository):
        self._repository = quota_repository

    async def check_quota(
        self, user_id: int, resource_type: str, amount: int
    ) -> bool:
        quota = await self._repository.get_by_user_and_type(user_id, resource_type)
        return quota.available >= amount
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
        # 通过接口检查配额
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

```python
# ❌ 禁止导出
__all__ = [
    "TrainingJobModel",           # ORM 模型
    "TrainingJobRepositoryImpl",  # 仓库实现
    "HyperPodClient",             # 外部客户端实现
]
```

---

## 6. 异常处理规范

### 6.1 异常继承体系

```python
# shared/domain/exceptions.py
class DomainError(Exception):
    """域层基础异常"""
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

### 6.2 模块异常定义

```python
# modules/{name}/domain/exceptions.py
from src.shared.domain import (
    DomainError,
    EntityNotFoundError,
    ValidationError,
)

class {Module}Error(DomainError):
    """模块基础异常"""
    pass

class {Entity}NotFoundError(EntityNotFoundError):
    """实体未找到 - 自动映射到 HTTP 404"""
    def __init__(self, entity_id: int):
        super().__init__(entity_type="{Entity}", entity_id=str(entity_id))

class Invalid{Entity}StateError(DomainError):
    """无效状态 - 自动映射到 HTTP 409"""
    pass
```

### 6.3 HTTP 状态码映射

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
    """单例模式，避免重复创建 AWS 客户端"""
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

## 9. 附录

### 9.1 快速参考卡片

```
┌────────────────────────────────────────────────────────┐
│            Modular Monolith 依赖速查                    │
├────────────────────────────────────────────────────────┤
│ ✅ 允许                                                │
│   • 导入 shared/* 任意内容                              │
│   • API 层导入 auth 的认证依赖                          │
│   • 通过 EventBus 发布/订阅事件                         │
│   • 依赖 shared/domain/interfaces 中定义的接口          │
├────────────────────────────────────────────────────────┤
│ ❌ 禁止                                                │
│   • Domain 层导入任何外部模块                           │
│   • 直接导入其他模块的 Service                          │
│   • 直接导入其他模块的 Repository 实现                  │
│   • 导入其他模块的 ORM Model                            │
├────────────────────────────────────────────────────────┤
│ 🔄 模块间通信                                          │
│   • 优先: EventBus (异步解耦)                          │
│   • 备选: shared/domain/interfaces (同步调用)          │
│   • 禁止: 直接依赖其他模块实现                          │
└────────────────────────────────────────────────────────┘
```

### 9.2 相关文档

| 文档 | 位置 | 说明 |
|------|------|------|
| 开发指南 | `backend/CLAUDE.md` | TDD 工作流、命令、代码风格 |
| 功能规范 | `specs/001-ai-training-platform/spec.md` | 术语标准、功能需求 |
| 数据模型 | `specs/001-ai-training-platform/data-model.md` | 数据库设计 |
| 架构合规测试 | `tests/unit/test_architecture_compliance.py` | 自动化验证 |

### 9.3 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2025-01-16 | 初始版本，整合分散规范 |
