# 后端架构规范 (Backend Architecture Standards)

> **职责**: 后端架构规范的单一真实源，定义分层规则、模块隔离和 DDD 模式。

> **版本**: 2.0
> **架构模式**: DDD + Modular Monolith + Clean Architecture
> **适用范围**: Python 后端项目

本文档是后端项目的**核心架构规范单一真实源 (Single Source of Truth)**。

<!-- CLAUDE: 项目特定配置请参考 PROJECT_CONFIG.ai-agents-platform.md -->

<!-- CLAUDE 占位符说明:
  {PROJECT}    → 项目源码根路径，如 src
  {Entity}     → 实体名称 PascalCase，如 User, TrainingJob
  {entity}     → 实体名称 snake_case，如 user, training_job
  {module}     → 模块名称，如 auth, training, quotas
  {other_module} → 其他模块名称（用于说明禁止的跨模块导入）
  {Capability} → 跨模块能力接口名 PascalCase，如 QuotaChecker
  {capability} → 跨模块能力接口名 snake_case，如 quota_checker
  {Client}     → 外部客户端名 PascalCase，如 HyperPod, S3
  {client}     → 外部客户端名 snake_case，如 hyperpod, s3
  {Service}    → 服务类名，如 TrainingJobService
  {RepoImpl}   → 仓库实现类名，如 UserRepositoryImpl
  {Error}      → 异常类名，如 QuotaError
  {entities}   → 实体复数形式，用于 ORM relationship
-->

---

## 0. 速查卡片

> Claude 生成代码时优先查阅此章节

### 0.1 依赖合法性速查矩阵

> **模块间通信**: 优先 EventBus (异步解耦)，备选 shared/interfaces (同步调用)，禁止直接依赖其他模块实现。

| 从 ↓ 导入 → | `shared/*` | `auth.api.dependencies` | 其他模块 Domain | 其他模块 Service | 其他模块 ORM Model |
|-------------|:----------:|:-----------------------:|:--------------:|:---------------:|:-----------------:|
| **Domain** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Application** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Infrastructure** | ✅ | ❌ | ❌ | ❌ | ⚠️ 仅外键 |
| **API** | ✅ | ✅ | ❌ | ❌ | ❌ |

**图例**: ✅ 允许 | ❌ 禁止 | ⚠️ 条件允许

### 0.2 数据模型选择速查

| 层级 | 组件类型 | 推荐方案 | 理由 |
|------|---------|---------|------|
| **Domain** | Entity | Pydantic | 业务规则验证、状态可变 |
| **Domain** | Value Object | dataclass(frozen) | 不可变、相等性基于值 |
| **Application** | DTO | dataclass | 内部传输、已验证数据 |
| **Infrastructure** | 外部响应 | Pydantic | 需验证和类型转换 |
| **Infrastructure** | ORM Model | SQLAlchemy | 持久化专用 |
| **API** | Request/Response | Pydantic | 外部输入验证、FastAPI 集成 |

**决策流程**:
```
数据来自外部？ ──是──► Pydantic
      │
     否
      ↓
需要业务验证？ ──是──► Pydantic
      │
     否
      ↓
需要不可变？ ──是──► dataclass(frozen=True)
      │
     否
      ↓
dataclass
```

### 0.3 PR Review 检查清单

**分层规则**:
- [ ] Domain 层没有外部框架依赖 (FastAPI, SQLAlchemy, boto3)
- [ ] Domain 层实体使用 Pydantic BaseModel 或 PydanticEntity 基类
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
- [ ] Application DTO 使用 dataclass (详见 §0.2)
- [ ] API Request/Response 使用 Pydantic (详见 §0.2)
- [ ] Repository 接口在 Domain 层，实现在 Infrastructure 层
- [ ] Domain Event 继承自 DomainEvent

**依赖注入**:
- [ ] 依赖注入层级正确 (Session → Repository → Service)
- [ ] 外部服务有对应的接口抽象
- [ ] 跨模块依赖通过 shared/interfaces 注入

---

## 1. 核心原则

### 1.1 架构模式融合

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

### 1.2 模块化原则

| 原则 | 说明 | 实践 |
|------|------|------|
| **模块自治** | 每个模块拥有独立的领域模型和业务逻辑 | 模块内 CRUD 完全独立 |
| **显式依赖** | 模块间依赖必须显式声明 | 通过接口定义依赖 |
| **最小知识** | 模块只暴露必要的接口 | 内部实现对外不可见 |
| **单向依赖** | 禁止循环依赖 | 使用事件解耦 |
| **高内聚低耦合** | 相关功能聚合在同一模块 | 按业务领域划分 |

<!-- CLAUDE: 项目模块列表见 PROJECT_CONFIG.ai-agents-platform.md -->

---

## 2. 分层规则

### 2.1 模块内部分层

每个业务模块遵循 Clean Architecture 四层结构：

```
┌──────────────────────────────────────────────────┐
│                   API Layer                       │  ← 暴露 HTTP 端点
│       (endpoints, schemas, middleware)            │
├──────────────────────────────────────────────────┤
│               Application Layer                   │  ← 业务用例编排
│     (services, dto, interfaces, exceptions)       │
├──────────────────────────────────────────────────┤
│                 Domain Layer                      │  ← 核心业务逻辑
│  (entities, value_objects, services, repositories)│
├──────────────────────────────────────────────────┤
│             Infrastructure Layer                  │  ← 技术实现
│         (persistence, external adapters)          │
└──────────────────────────────────────────────────┘
```

### 2.2 依赖规则 (The Dependency Rule)

| 层级 | 可以依赖 | 禁止依赖 |
|------|---------|---------|
| **Domain** | Pydantic (数据验证), shared/domain | FastAPI, SQLAlchemy, boto3 |
| **Application** | Domain | FastAPI, SQLAlchemy, boto3 |
| **Infrastructure** | Domain, Application | - |
| **API (Presentation)** | Application, Domain (类型) | Infrastructure (通过 DI) |

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

## 3. 模块隔离规则

### 3.1 黄金法则

| 规则 | 说明 | 强制性 |
|------|------|--------|
| **R1** | 模块的 Domain 层**绝对不能**导入任何其他模块代码 | 🔴 强制 |
| **R2** | 模块的 Application 层只能依赖**接口**，不能依赖具体实现 | 🔴 强制 |
| **R3** | 模块间通信必须通过**事件总线**或**共享接口** | 🔴 强制 |
| **R4** | `auth` 模块的认证依赖是**唯一例外**，可被其他模块 API 层导入 | 🟡 例外 |
| **R5** | Domain Events 作为模块公开契约，其他模块 **Application 层** 可导入用于事件订阅 | 🟡 例外 |

### 3.2 允许的依赖

#### 共享内核依赖

所有模块可以导入 `shared/` 下的内容：

```python
# ✅ Domain 层共享
from {PROJECT}.shared.domain import (
    BaseEntity, PydanticEntity,  # 可选基类，也可直接使用 pydantic.BaseModel
    IRepository,
    DomainError, EntityNotFoundError, ValidationError,
    DomainEvent, event_bus, event_handler,
)

# ✅ Infrastructure 层共享
from {PROJECT}.shared.infrastructure import get_db, get_settings, PydanticRepository

# ✅ API 层共享
from {PROJECT}.shared.api import domain_exception_handler
from {PROJECT}.shared.api.schemas import EntitySchema, PaginatedResponse
```

**Shared Kernel 约束**:
- `shared/` 只包含技术基础设施和跨模块抽象，**禁止包含任何业务逻辑**
- 跨模块接口只定义契约，实现放在具体模块的 Infrastructure 层

#### Auth 模块特殊依赖（唯一例外）

其他模块的 **API 层** 可以导入 auth 的认证依赖：

```python
# ✅ 仅允许在 API 层导入
from {PROJECT}.modules.auth.api.dependencies import (
    get_current_active_user,
    require_admin,
)
```

### 3.3 禁止的依赖

```python
# ❌ 禁止：跨模块直接导入 (以下均为反面示例)
from {PROJECT}.modules.{other_module}.application.services import {Service}       # ❌ Service
from {PROJECT}.modules.{other_module}.domain.entities import {Entity}             # ❌ Entity
from {PROJECT}.modules.{other_module}.infrastructure.repositories import {RepoImpl}  # ❌ Repository
from {PROJECT}.modules.{other_module}.domain import {Error}                       # ❌ Domain 层绝对禁止！
```

#### 技术例外：ORM 模型外键关系

ORM 模型文件（`*_model.py`）**允许**导入其他模块的 ORM 模型，用于定义外键关系：

```python
# ✅ 允许：ORM 模型定义外键关系
# modules/{module}/infrastructure/persistence/models/{entity}_model.py
from {PROJECT}.modules.auth.infrastructure.persistence.models import UserModel

class {Entity}Model(Base):
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="{entities}")
```

---

## 4. 模块间通信

### 4.1 DDD 集成模式决策矩阵

| 场景 | 推荐模式 | 实现方式 |
|------|---------|---------|
| 实时同步调用 | **Open Host Service** | `shared/domain/interfaces/` |
| 异步通知 | **Published Language** | Domain Events + EventBus |
| 复杂外部系统集成 | **Anti-Corruption Layer** | Infrastructure 适配器 |
| 高度耦合共享概念 | **Shared Kernel** | `shared/domain/` |

### 4.2 事件驱动通信（推荐）

```python
# 1. 定义域事件 (modules/{module}/domain/events.py)
@dataclass
class {Entity}CompletedEvent(DomainEvent):
    entity_id: int
    owner_id: int

# 2. 发布事件 (Application Service 中)
entity.mark_completed()
await event_bus.publish_async({Entity}CompletedEvent(entity_id=..., owner_id=...))

# 3. 订阅事件 (其他模块 Application Service)
@event_handler({Entity}CompletedEvent)
async def on_{entity}_completed(self, event: {Entity}CompletedEvent):
    # 处理逻辑...
```

### 4.3 共享接口通信

当需要同步调用时，通过 `shared/domain/interfaces/` 定义接口。

> **📌 接口位置区分**:
> - `shared/domain/interfaces/`: **跨模块能力接口**，供多个模块依赖（如 `IQuotaChecker`）
> - `modules/{module}/application/interfaces/`: **模块内外部服务抽象**，仅供本模块使用（如 `IS3Client`）

```python
# shared/domain/interfaces/{interface}.py
from abc import ABC, abstractmethod

class I{Capability}(ABC):
    """{能力}接口 - 供其他模块使用。"""

    @abstractmethod
    async def check(self, user_id: int, resource_type: str, amount: int) -> bool:
        pass
```

```python
# modules/{module}/application/services/{entity}_service.py
from {PROJECT}.shared.domain.interfaces import I{Capability}

class {Entity}Service:
    def __init__(
        self,
        repository: I{Entity}Repository,
        capability: I{Capability},  # 依赖接口，不依赖实现
    ):
        self._repository = repository
        self._capability = capability
```

<!-- CLAUDE: 核心域事件清单见 PROJECT_CONFIG.ai-agents-platform.md -->

---

## 5. DDD 战术模式

### 5.1 Entity 实体

**推荐方式 - PydanticEntity (Pydantic V2)**:

```python
from pydantic import Field
from {PROJECT}.shared.domain import PydanticEntity  # 或直接继承 pydantic.BaseModel

class {Entity}(PydanticEntity):
    """{实体}实体 - 有唯一身份标识。"""

    name: str = Field(min_length=3, max_length=64)
    status: {Entity}Status = {Entity}Status.ACTIVE

    def activate(self) -> None:
        """激活{实体}。"""
        self.status = {Entity}Status.ACTIVE
        self.touch()  # 更新 updated_at

    def __eq__(self, other: object) -> bool:
        """实体相等性基于 ID。"""
        if not isinstance(other, {Entity}):
            return False
        return self.id == other.id
```

**Entity 规范**:
- 继承 `PydanticEntity`，自动获得 `id`, `created_at`, `updated_at`
- 状态转换逻辑在 Entity 内部，**禁止**依赖外部服务或数据库
- 只抛出 Domain 异常，**禁止** `ValueError` 等通用异常

> **📌 关于 Pydantic**: Domain 层允许直接使用 Pydantic 进行数据验证。Pydantic 被视为 Python 生态的标准数据验证工具，与 dataclass 同等级别，不属于"外部框架依赖"。

### 5.2 Value Object 值对象

```python
import re
from dataclasses import dataclass
from {PROJECT}.shared.domain import ValidationError

@dataclass(frozen=True)  # frozen=True 确保不可变
class Email:
    """邮箱值对象 - 无身份标识，相等性基于值。"""

    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}$", self.value):
            raise ValidationError(f"无效的邮箱格式: {self.value}")

    @property
    def domain(self) -> str:
        return self.value.split("@")[1]
```

### 5.3 Domain Service 领域服务

**何时使用领域服务**:
- 业务逻辑涉及多个实体或聚合
- 逻辑不自然地属于任何单一实体
- 需要协调多个值对象的计算

```python
# modules/{module}/domain/services/pricing_service.py
from dataclasses import dataclass
from {PROJECT}.shared.domain import ValidationError

@dataclass
class PricingService:
    """定价领域服务 - 跨实体的定价计算逻辑。"""
    tax_rate: float = 0.1

    def calculate_total(self, base_price: Money, discount: Discount | None, quantity: int) -> Money:
        if quantity <= 0:
            raise ValidationError("数量必须大于 0")
        subtotal = base_price.multiply(quantity)
        if discount:
            subtotal = discount.apply(subtotal)
        return subtotal.add_tax(self.tax_rate)
```

**领域服务规范**:
- 无状态，不持有任何实体引用
- 只依赖值对象和领域异常
- **禁止**依赖 Repository 或任何基础设施
- 使用 `@dataclass` 定义，便于测试和依赖注入

### 5.4 Repository 仓库

**推荐方式 - PydanticRepository**:

```python
from {PROJECT}.shared.infrastructure import PydanticRepository

class {Entity}RepositoryImpl(PydanticRepository[{Entity}, {Entity}Model, int], I{Entity}Repository):
    """{实体}仓库实现 - 自动 Entity ↔ Model 转换。"""

    _entity_class = {Entity}
    _updatable_fields = ["name", "status", ...]

    def __init__(self, session: AsyncSession):
        super().__init__(session, {Entity}Model)
```

**Repository 规范**:
- 接口定义在 Domain 层，实现在 Infrastructure 层 (`infrastructure/persistence/repositories/`)
- 内置 CRUD：`get_by_id`, `create`, `update`, `delete`, `exists`
- 通过 `_updatable_fields` 控制可更新字段

---

## 6. 模块结构模板

### 6.1 目录结构

```
modules/{module}/
├── __init__.py             # 模块公开 API 导出
├── api/
│   ├── __init__.py
│   ├── endpoints.py        # FastAPI router
│   ├── dependencies.py     # 依赖注入函数
│   ├── middleware/         # 模块级中间件
│   │   └── __init__.py
│   └── schemas/
│       ├── __init__.py
│       ├── requests.py     # 请求模型
│       └── responses.py    # 响应模型
├── application/
│   ├── __init__.py
│   ├── dto/                # 数据传输对象
│   │   └── __init__.py
│   ├── interfaces/         # 端口接口 (模块内外部服务抽象，如 S3Client 接口)
│   │   └── __init__.py
│   ├── exceptions/         # 应用层异常
│   │   └── __init__.py
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
│   ├── services/           # 领域服务
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── {entity}_repository.py  # 接口
│   ├── events.py
│   └── exceptions.py
└── infrastructure/
    ├── __init__.py
    ├── persistence/        # 数据持久化
    │   ├── __init__.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── {entity}_model.py
    │   └── repositories/
    │       ├── __init__.py
    │       └── {entity}_repository_impl.py
    └── external/           # 外部服务适配器
        └── __init__.py
```

### 6.2 文件命名规范

| 类型 | 命名规范 | 示例 |
|------|---------|------|
| 实体 | `{entity}.py` | `user.py` |
| 仓库接口 | `{entity}_repository.py` | `user_repository.py` |
| 仓库实现 | `{entity}_repository_impl.py` | `user_repository_impl.py` |
| ORM 模型 | `{entity}_model.py` | `user_model.py` |
| 应用服务 | `{entity}_service.py` | `user_service.py` |
| 领域服务 | `{domain}_service.py` | `pricing_service.py` |
| 应用层异常 | `exceptions.py` 或按类型拆分 | `exceptions.py` |
| 外部适配器 | `{service}_adapter.py` | `s3_adapter.py` |
| 中间件 | `{purpose}_middleware.py` | `logging_middleware.py` |

### 6.3 `__init__.py` 导出规则

每个模块必须在 `__init__.py` 明确定义公开 API：

```python
# modules/{module}/__init__.py
from .api.endpoints import router
from .api.dependencies import get_{entity}_service
from .application.services import {Entity}Service
from .domain.entities import {Entity}
from .domain.events import {Entity}CompletedEvent, {Entity}FailedEvent

__all__ = [
    # API
    "router",
    "get_{entity}_service",
    # Application
    "{Entity}Service",
    # Domain
    "{Entity}",
    # Events (供其他模块订阅)
    "{Entity}CompletedEvent",
    "{Entity}FailedEvent",
]
```

**禁止导出**:
- `{Entity}Model` (ORM 模型)
- `{Entity}RepositoryImpl` (仓库实现)
- 外部客户端实现

---

## 7. 依赖注入

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

### 7.2 依赖函数模板

```python
# modules/{module}/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from {PROJECT}.shared.infrastructure import get_db
from {PROJECT}.shared.domain.interfaces import I{Capability}

# Repository 依赖
async def get_{entity}_repository(session: AsyncSession = Depends(get_db)) -> I{Entity}Repository:
    return {Entity}RepositoryImpl(session)

# 跨模块能力依赖 (可选)
async def get_{capability}(session: AsyncSession = Depends(get_db)) -> I{Capability}:
    return {Capability}Impl({Capability}RepositoryImpl(session))

# Service 依赖 (组合 Repository + 跨模块能力)
async def get_{entity}_service(
    repository: I{Entity}Repository = Depends(get_{entity}_repository),
    capability: I{Capability} = Depends(get_{capability}),  # 可选
) -> {Entity}Service:
    return {Entity}Service(repository=repository, capability=capability)
```

### 7.3 外部客户端 Singleton 模式

```python
from functools import lru_cache
from {PROJECT}.shared.infrastructure import get_settings

@lru_cache(maxsize=1)
def get_{client}_client() -> {Client}Client:
    """单例模式，避免重复创建客户端。"""
    settings = get_settings()
    return {Client}Client(region=settings.aws_region)
```

---

## 8. 异常处理

### 8.1 异常继承体系

```python
# shared/domain/exceptions.py
class DomainError(Exception):
    """域层基础异常。"""
    pass

class EntityNotFoundError(DomainError):
    """实体未找到 - HTTP 404"""
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(f"{entity_type} with id {entity_id} not found")

# 以下异常无额外逻辑，单行定义
class ValidationError(DomainError): pass              # HTTP 422
class DuplicateEntityError(DomainError): pass         # HTTP 409
class InvalidStateTransitionError(DomainError): pass  # HTTP 409
class ResourceQuotaExceededError(DomainError): pass   # HTTP 429
```

### 8.2 HTTP 状态码映射

异常会被 `shared/api/exception_handlers.py` 自动映射：

| 异常类型 | HTTP 状态码 | 场景 |
|---------|-------------|------|
| `EntityNotFoundError` | 404 | 资源不存在 |
| `DuplicateEntityError` | 409 | 资源已存在 |
| `InvalidStateTransitionError` | 409 | 状态转换非法 |
| `ValidationError` | 422 | 参数验证失败 |
| `ResourceQuotaExceededError` | 429 | 配额不足 |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `PROJECT_CONFIG.ai-agents-platform.md` | 项目特定配置 (模块列表、技术栈、域事件) |
| `CLAUDE.md` | TDD 工作流、命令、代码风格 |
| `rules/code-style.md` | 命名规范、类型提示 |
| `rules/testing.md` | TDD 循环、测试分层 |
| `rules/security.md` | 安全最佳实践 |
| `rules/sdk-first.md` | SDK 优先原则 |
