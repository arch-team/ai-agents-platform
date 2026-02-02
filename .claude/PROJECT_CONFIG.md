# 项目配置 (Project Configuration)

> 本文件包含项目特定配置，供 Claude Code 在应用架构规范时参考。
> 架构规范详见 [rules/architecture-backend.md](rules/architecture-backend.md)

---

## 项目信息

| 配置项 | 值 |
|--------|-----|
| **项目名称** | AI Agents Platform |
| **项目描述** | 基于 AWS HyperPod 的 ML 训练平台后端服务 |
| **架构模式** | DDD + Modular Monolith + Clean Architecture |
| **源码根路径** | `src` |
| **模块路径** | `src/modules` |
| **共享路径** | `src/shared` |

---

## 技术栈

| 类别 | 技术选型 | 版本要求 |
|------|---------|---------|
| **Web 框架** | FastAPI | 0.110+ |
| **ORM** | SQLAlchemy 2.0 (async) | 2.0+ |
| **数据库** | MySQL 8.0+ (Aurora MySQL 3.x 兼容) | 8.0+ |
| **Python** | Python | 3.11+ |
| **数据验证** | Pydantic | v2 |
| **外部服务** | AWS SageMaker HyperPod | - |

---

## 业务模块

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

## 核心域事件

| 模块 | 事件 | 触发场景 | 订阅者 |
|------|------|---------|--------|
| **training** | `TrainingJobSubmittedEvent` | 任务提交 | quotas, audit |
| **training** | `TrainingJobCompletedEvent` | 任务完成 | audit, monitoring |
| **training** | `TrainingJobFailedEvent` | 任务失败 | audit, monitoring |
| **quotas** | `QuotaExceededEvent` | 配额超限 | monitoring |
| **auth** | `UserCreatedEvent` | 用户创建 | quotas (初始化配额) |
| **models** | `ModelPublishedEvent` | 模型发布 | audit |

---

## 导入路径配置

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

### Auth 模块认证依赖 (唯一跨模块例外)

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

| 服务 | 用途 | 适配器位置 |
|------|------|-----------|
| AWS SageMaker HyperPod | ML 训练任务调度 | `infrastructure/external/aws/hyperpod/` |
| AWS S3 | 数据集和模型存储 | `infrastructure/external/aws/s3/` |
| AWS DynamoDB | 配置存储 | `infrastructure/external/aws/dynamodb/` |
| AWS SES | 邮件通知 | `infrastructure/external/email/` |

---

## 违规检测模式

Claude 应检测并阻止以下 import 模式：

```python
# 违规模式正则表达式
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

# 允许的例外
ALLOWED_EXCEPTIONS = [
    # ORM 模型外键关系 (仅 *_model.py 文件)
    r"infrastructure/models/.*_model\.py:.*from src\.modules\.[\w]+\.infrastructure\.models import",
    # Auth 认证依赖 (仅 API 层)
    r"api/.*:.*from src\.modules\.auth\.api\.(dependencies|current_user) import",
]
```

---

## 架构合规测试

测试位于 `tests/unit/test_architecture_compliance.py`：

| 测试类 | 验证规则 |
|--------|---------|
| `TestCleanArchitectureLayers` | 分层依赖方向 |
| `TestModuleDomainLayerIsolation` | R1: Domain 层隔离 |
| `TestModuleApplicationLayerDependencies` | R2: Application 层依赖接口 |
| `TestModuleApiLayerAuthDependency` | R4: Auth 依赖例外 |
| `TestModuleInfrastructureLayerIsolation` | Infrastructure 层隔离 |
| `TestModulePublicApiExports` | 模块 `__all__` 导出 |

```bash
# 运行架构合规测试
pytest tests/unit/test_architecture_compliance.py -v
```
