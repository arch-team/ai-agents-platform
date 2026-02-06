# 项目配置 - AI Agents Platform

> **职责**: AI Agents Platform 项目的特定配置，包含模块列表和导入路径。

> **定位**: 本文件是 CLAUDE.md 的补充，包含**项目特定的业务配置**。
> **原则**: 通用规范放 `rules/`，项目特定信息放此处。
> 架构规范详见 [rules/architecture.md](rules/architecture.md)

---

## 项目信息

| 配置项 | 值 |
|--------|-----|
| **项目名称** | ai-agents-platform |
| **项目描述** | AI Agents Platform - 基于Amazon Bedrock AgentCore的企业级AI Agents平台 |
| **架构模式** | DDD + Modular Monolith + Clean Architecture |
| **Python 版本** | >=3.11 |
| **源码根路径** | `src` |
| **模块路径** | `src/modules` |
| **共享路径** | `src/shared` |

---

## 技术栈补充

> **注意**: 核心技术栈定义在 CLAUDE.md，此处列出版本要求和项目特有选型。

| 类别 | 技术选型 | 版本要求 |
|------|---------|---------|
| **Web 框架** | FastAPI | >=0.110.0 |
| **ASGI 服务器** | Uvicorn | >=0.27.0 |
| **数据验证** | Pydantic | >=2.6.0 |
| **ORM** | SQLAlchemy (async) | >=2.0.25 |
| **数据库迁移** | Alembic | >=1.13.0 |
| **数据库** | MySQL 8.0+ (Aurora MySQL 3.x 兼容) | 8.0+ |
| **AWS SDK** | boto3 | >=1.34.0 |
| **认证** | python-jose, passlib | - |
| **日志** | structlog | >=24.1.0 |

---

## 业务模块

> **维护提示**: 新增模块时同步更新此表和 `src/modules/` 目录。

| 模块 | 职责 | 核心实体 |
|------|------|---------|
| `auth` | 用户认证与授权 | `User` |
| `shared` | 共享内核 | `BaseEntity`, `DomainEvent` |
<!-- 示例：
| `orders` | 订单管理 | `Order`, `OrderItem` |
| `products` | 商品管理 | `Product`, `Category` |
-->

---

## 核心域事件

> **设计原则**: 事件用于模块间解耦通信，订阅者不应直接依赖发布者的实现。

| 模块 | 事件 | 触发场景 | 订阅者 |
|------|------|---------|--------|
| `auth` | `UserCreatedEvent` | 用户创建 | - |
<!-- 示例：
| `orders` | `OrderCreatedEvent` | 订单创建 | audit, notification |
| `orders` | `OrderCompletedEvent` | 订单完成 | billing, audit |
-->

---

## 导入路径配置

> **原则**: 参考 [rules/architecture.md](rules/architecture.md) §3 模块隔离规则。

### 共享内核导入

```python
# Domain 层共享
from src.shared.domain import (
    BaseEntity, PydanticEntity,
    IRepository,
    DomainError, EntityNotFoundError, ValidationError,
    DomainEvent, event_bus, event_handler,
    IQuotaChecker,  # 跨模块接口
)

# Infrastructure 层共享
from src.shared.infrastructure import get_db, get_settings, PydanticRepository
from src.shared.infrastructure.security import hash_password, verify_password

# API 层共享
from src.shared.api import domain_exception_handler
from src.shared.api.schemas import EntitySchema, PaginatedResponse
```

### 认证依赖 (唯一跨模块例外)

```python
# 仅允许在 API 层导入
from src.modules.auth.api.dependencies import (
    get_current_active_user,
    require_admin,
    require_engineer,
)
from src.modules.auth.api.current_user import CurrentUser
```

---

## 外部服务配置

> **位置约定**: 所有外部服务适配器放在 `infrastructure/external/` 下。

| 服务 | 用途 | 适配器位置 |
|------|------|-----------|
| AWS S3 | 数据集和模型存储 | `infrastructure/external/aws/s3/` |
| AWS DynamoDB | 配置存储 | `infrastructure/external/aws/dynamodb/` |
| AWS SES | 邮件通知 | `infrastructure/external/email/` |

---

## 架构合规规则

> **详细规则**: 见 [rules/architecture.md](rules/architecture.md) §0.1 依赖合法性速查矩阵。

### 违规检测 (Claude 自动检查)

| 违规类型 | 模式 | 严重级别 |
|---------|------|---------|
| 跨模块 Service 导入 | `from src.modules.X.application.services` | 🔴 阻止 |
| 跨模块 Entity 导入 | `from src.modules.X.domain.entities` | 🔴 阻止 |
| Domain 层导入外部框架 | `domain/` 文件中 `from fastapi/sqlalchemy` | 🔴 阻止 |
| 跨模块 Repository 实现导入 | `from src.modules.X.infrastructure.repositories` | 🟡 警告 |

### 允许的例外

- **ORM 外键关系**: `*_model.py` 中可导入其他模块的 ORM Model
- **Auth 认证**: API 层可导入 `auth.api.dependencies`

---

## 架构合规测试

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
