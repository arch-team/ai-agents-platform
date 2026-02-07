# 后端架构规范 (Backend Architecture Standards)

> **职责**: 后端架构规范的单一真实源，定义分层规则、模块隔离和 DDD 模式。

> **架构模式**: DDD + Modular Monolith + Clean Architecture
> **适用范围**: Python 后端项目

<!-- CLAUDE 占位符: {PROJECT}=src, {Entity}/{entity}=实体名, {module}=模块名 -->

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

完整检查清单见 [checklist.md](checklist.md) §分层与架构

---

## 1. 核心原则

### 1.1 架构模式融合

```
DDD (战术设计)         → Entity, Value Object, Aggregate, Domain Event, Repository
Modular Monolith (模块化) → 垂直切分业务模块，模块间松耦合，共享基础设施
Clean Architecture (分层) → 依赖倒置，核心业务与外部依赖隔离
```

### 1.2 模块化原则

| 原则 | 说明 |
|------|------|
| **模块自治** | 每个模块拥有独立的领域模型和业务逻辑 |
| **显式依赖** | 模块间依赖必须通过接口显式声明 |
| **最小知识** | 模块只暴露必要的接口，内部实现不可见 |
| **单向依赖** | 禁止循环依赖，使用事件解耦 |

---

## 2. 分层规则

### 2.1 模块内部四层结构

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

### 2.2 依赖规则

| 层级 | 可以依赖 | 禁止依赖 |
|------|---------|---------|
| **Domain** | Pydantic (数据验证), shared/domain | FastAPI, SQLAlchemy, boto3 |
| **Application** | Domain | FastAPI, SQLAlchemy, boto3 |
| **Infrastructure** | Domain, Application | - |
| **API (Presentation)** | Application, Domain (类型) | Infrastructure (通过 DI) |

### 2.3 依赖方向

```
模块内: API 层 → Application 层 → Domain 层 ← Infrastructure 层
跨模块: modules/A ───X───► modules/B (禁止横向依赖)
              └──► shared/ (唯一允许的共享依赖)
```

- **API 层**: 只能通过 Application Services 执行业务操作
- **Infrastructure**: 同时实现 Domain 层 Repository 接口和 Application 层外部服务接口

---

## 3. 模块隔离规则

### 3.1 黄金法则

| 规则 | 说明 | 强制性 |
|------|------|--------|
| **R1** | 模块的 Domain 层**绝对不能**导入任何其他模块代码 | 🔴 强制 |
| **R2** | 模块的 Application 层只能依赖**接口**，不能依赖具体实现 | 🔴 强制 |
| **R3** | 模块间通信必须通过**事件总线**或**共享接口** | 🔴 强制 |
| **R4** | `auth` 模块的认证依赖是**唯一例外**，可被其他模块 API 层导入 | 🟡 例外 |
| **R5** | Domain Events 作为模块公开契约，其他模块 Application 层可导入用于事件订阅 | 🟡 例外 |

### 3.2 允许的共享内核依赖

```python
# ✅ 所有模块可导入 shared/
from {PROJECT}.shared.domain import PydanticEntity, IRepository, DomainError, DomainEvent, event_bus
from {PROJECT}.shared.infrastructure import get_db, get_settings, PydanticRepository
from {PROJECT}.shared.api import domain_exception_handler
```

**约束**: `shared/` 只包含技术基础设施和跨模块抽象，**禁止包含任何业务逻辑**

### 3.3 禁止的依赖

```python
# ❌ 禁止：跨模块直接导入
from {PROJECT}.modules.{other_module}.application.services import {Service}       # ❌
from {PROJECT}.modules.{other_module}.domain.entities import {Entity}             # ❌
from {PROJECT}.modules.{other_module}.infrastructure.repositories import {RepoImpl}  # ❌
```

**唯一例外**: ORM 模型文件 (`*_model.py`) 允许导入其他模块 ORM Model 定义外键关系

---

## 4. 模块间通信

### 4.1 集成模式决策

| 场景 | 推荐模式 | 实现方式 |
|------|---------|---------|
| 实时同步调用 | Open Host Service | `shared/domain/interfaces/` |
| 异步通知 | Published Language | Domain Events + EventBus |
| 复杂外部系统 | Anti-Corruption Layer | Infrastructure 适配器 |

### 4.2 事件驱动通信（推荐）

```python
# 定义 → 发布 → 订阅
@dataclass
class {Entity}CompletedEvent(DomainEvent):
    entity_id: int
    owner_id: int

# 发布: await event_bus.publish_async({Entity}CompletedEvent(...))
# 订阅: @event_handler({Entity}CompletedEvent)
```

#### 事件可靠性要求

| 要求 | 说明 | 实现方式 |
|------|------|---------|
| **幂等性** | 处理器必须能安全重复执行 | 通过 `event_id` 去重，处理前检查是否已处理 |
| **重试策略** | 失败时指数退避重试 | `max_retries=3`, 退避间隔 `1s → 2s → 4s` |
| **Outbox Pattern** | 事件与业务操作原子性提交 | 事件先写入 `outbox` 表，后台轮询发布 |
| **顺序保证** | 同一聚合根的事件需有序处理 | 按 `aggregate_id` 分区 |

### 4.3 接口位置区分

- `shared/domain/interfaces/`: **跨模块能力接口**（如 `IQuotaChecker`）
- `modules/{module}/application/interfaces/`: **模块内外部服务抽象**（如 `IS3Client`）

---

## 5. DDD 战术模式

### 5.1 Entity 实体

继承 `PydanticEntity`，自动获得 `id`, `created_at`, `updated_at`。

**规范**: 必须配置 `ConfigDict(validate_assignment=True)` | 状态转换在 Entity 内部（调用 `self.touch()` 更新时间戳） | 禁止依赖外部服务 | 只抛 Domain 异常 | Pydantic 视为标准工具不属于"外部框架"

### 5.2 Value Object 值对象

使用 `@dataclass(frozen=True)` 确保不可变，相等性基于值。

### 5.3 Domain Service 领域服务

使用 `@dataclass` 定义，无状态 | 只依赖值对象和领域异常 | 禁止依赖 Repository

### 5.4 Repository 仓库

接口在 Domain 层 (`I{Entity}Repository(IRepository[{Entity}, int])`)，实现在 Infrastructure 层 (`{Entity}RepositoryImpl(PydanticRepository[...])`)。

**规范**: `IRepository[E, ID]` 泛型接口定义在 shared | `PydanticRepository` 内置 CRUD | 通过 `_updatable_fields` 白名单控制可更新字段

---

## 6. 模块结构模板

### 6.1 目录结构

```
modules/{module}/
├── __init__.py             # 模块公开 API 导出
├── api/
│   ├── endpoints.py        # FastAPI router
│   ├── dependencies.py     # 依赖注入函数
│   ├── middleware/
│   └── schemas/
│       ├── requests.py     # 请求模型 (Pydantic)
│       └── responses.py    # 响应模型 (Pydantic)
├── application/
│   ├── dto/                # 数据传输对象 (dataclass)
│   ├── interfaces/         # 模块内外部服务抽象
│   ├── exceptions/         # 应用层异常
│   └── services/
│       └── {entity}_service.py
├── domain/
│   ├── entities/{entity}.py
│   ├── value_objects/
│   ├── services/           # 领域服务
│   ├── repositories/{entity}_repository.py  # 接口
│   ├── events.py
│   └── exceptions.py
└── infrastructure/
    ├── persistence/
    │   ├── models/{entity}_model.py
    │   └── repositories/{entity}_repository_impl.py
    └── external/           # 外部服务适配器
```

### 6.2 文件命名规范

| 类型 | 命名规范 | 示例 |
|------|---------|------|
| 实体 | `{entity}.py` | `user.py` |
| 仓库接口 | `{entity}_repository.py` | `user_repository.py` |
| 仓库实现 | `{entity}_repository_impl.py` | `user_repository_impl.py` |
| ORM 模型 | `{entity}_model.py` | `user_model.py` |
| 应用服务 | `{entity}_service.py` | `user_service.py` |
| 外部适配器 | `{service}_adapter.py` | `s3_adapter.py` |

### 6.3 `__init__.py` 导出规则

导出: `router`, Service, Entity, Domain Events | 禁止导出: ORM Model, RepositoryImpl, 外部客户端实现

---

## 7. 依赖注入

```
Layer 1: Database Session (get_db)
    → Layer 2: Repository (get_xxx_repository)
    → Layer 3: External Client (get_xxx_client) - 推荐 @lru_cache Singleton
    → Layer 4: Application Service (get_xxx_service)
    → Layer 5: Permission Check (require_xxx)
```

---

## 8. 异常处理

异常在 `shared/domain/exceptions.py` 定义，由 `shared/api/exception_handlers.py` 自动映射 HTTP 状态码：

| 异常类型 | HTTP 状态码 | 场景 |
|---------|-------------|------|
| `EntityNotFoundError` | 404 | 资源不存在 |
| `DuplicateEntityError` | 409 | 资源已存在 |
| `InvalidStateTransitionError` | 409 | 状态转换非法 |
| `ValidationError` | 422 | 参数验证失败 |
| `ResourceQuotaExceededError` | 429 | 配额不足 |

---

## 9. 架构合规测试

> **测试位置**: `tests/unit/test_architecture_compliance.py`

| 测试类 | 验证规则 |
|--------|---------|
| `TestCleanArchitectureLayers` | 分层依赖方向 |
| `TestModuleDomainLayerIsolation` | Domain 层绝对隔离 |
| `TestModuleApplicationLayerDependencies` | Application 层依赖接口 |
| `TestModuleApiLayerAuthDependency` | Auth 依赖例外验证 |

```bash
# 运行架构合规测试
uv run pytest tests/unit/test_architecture_compliance.py -v
```
