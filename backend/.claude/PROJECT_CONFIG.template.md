# 项目配置模板 (Project Configuration Template)

<!--
使用说明：
1. 复制此模板到新项目的 .claude/ 目录
2. 替换所有 {{PLACEHOLDER}} 占位符
3. 删除不适用的章节
4. 保持与 CLAUDE.md 的单向引用（CLAUDE.md → PROJECT_CONFIG.md）
-->

> **定位**: 本文件是 CLAUDE.md 的补充，包含**项目特定的业务配置**。
> **原则**: 通用规范放 `rules/`，项目特定信息放此处。
> 架构规范详见 [rules/architecture.md](rules/architecture.md)

---

## 项目信息

<!-- 替换为实际项目信息 -->
| 配置项 | 值 |
|--------|-----|
| **项目名称** | {{PROJECT_NAME}} |
| **项目描述** | {{PROJECT_DESCRIPTION}} |
| **架构模式** | {{ARCHITECTURE_PATTERN}} |
| **源码根路径** | `{{SRC_ROOT}}` |
| **模块路径** | `{{SRC_ROOT}}/modules` |
| **共享路径** | `{{SRC_ROOT}}/shared` |

---

## 技术栈补充

> **注意**: 核心技术栈定义在 CLAUDE.md，此处仅列出**项目特有**的技术选型。

| 类别 | 技术选型 | 用途说明 |
|------|---------|---------|
| **数据库** | {{DATABASE}} | {{DATABASE_PURPOSE}} |
| **外部服务** | {{EXTERNAL_SERVICE}} | {{SERVICE_PURPOSE}} |
<!-- 添加其他项目特有技术 -->

---

## 业务模块

> **维护提示**: 新增模块时同步更新此表和 `{{SRC_ROOT}}/modules/` 目录。

| 模块 | 职责 | 核心实体 |
|------|------|---------|
| `auth` | 用户认证与授权 | `User` |
| `{{MODULE_1}}` | {{MODULE_1_DESC}} | `{{ENTITY_1}}` |
| `{{MODULE_2}}` | {{MODULE_2_DESC}} | `{{ENTITY_2}}` |
| `shared` | 共享内核 (必须保留) | `BaseEntity`, `DomainEvent` |

---

## 核心域事件

> **设计原则**: 事件用于模块间解耦通信，订阅者不应直接依赖发布者的实现。

| 模块 | 事件 | 触发场景 | 订阅者 |
|------|------|---------|--------|
| `{{MODULE}}` | `{{Entity}}CreatedEvent` | 实体创建 | audit |
| `{{MODULE}}` | `{{Entity}}CompletedEvent` | 流程完成 | audit, monitoring |
| `{{MODULE}}` | `{{Entity}}FailedEvent` | 流程失败 | audit, monitoring |
| `auth` | `UserCreatedEvent` | 用户创建 | quotas (必须) |

<!-- 示例 (当前项目):
| training | TrainingJobSubmittedEvent | 任务提交 | quotas, audit |
| quotas | QuotaExceededEvent | 配额超限 | monitoring |
-->

---

## 导入路径配置

> **原则**: 参考 [rules/architecture.md](rules/architecture.md) §3 模块隔离规则。

### 共享内核导入

```python
# Domain 层共享
from {{SRC_ROOT}}.shared.domain import (
    BaseEntity, PydanticEntity,
    IRepository,
    DomainError, EntityNotFoundError, ValidationError,
    DomainEvent, event_bus, event_handler,
    # 跨模块接口 (按需添加)
)

# Infrastructure 层共享
from {{SRC_ROOT}}.shared.infrastructure import get_db, get_settings, PydanticRepository

# API 层共享
from {{SRC_ROOT}}.shared.api import domain_exception_handler
from {{SRC_ROOT}}.shared.api.schemas import EntitySchema, PaginatedResponse
```

### 认证依赖 (唯一跨模块例外)

```python
# 仅允许在 API 层导入
from {{SRC_ROOT}}.modules.auth.api.dependencies import (
    get_current_active_user,
    # 按需添加角色检查函数
)
```

---

## 外部服务配置

> **位置约定**: 所有外部服务适配器放在 `infrastructure/external/` 下。

| 服务 | 用途 | 适配器位置 |
|------|------|-----------|
| {{SERVICE_1}} | {{SERVICE_1_PURPOSE}} | `infrastructure/external/{{service_1}}/` |
| {{SERVICE_2}} | {{SERVICE_2_PURPOSE}} | `infrastructure/external/{{service_2}}/` |

---

## 架构合规规则

> **详细规则**: 见 [rules/architecture.md](rules/architecture.md) §0.1 依赖合法性速查矩阵。

### 违规检测 (Claude 自动检查)

| 违规类型 | 模式 | 严重级别 |
|---------|------|---------|
| 跨模块 Service 导入 | `from {{SRC_ROOT}}.modules.X.application.services` | 🔴 阻止 |
| 跨模块 Entity 导入 | `from {{SRC_ROOT}}.modules.X.domain.entities` | 🔴 阻止 |
| Domain 层导入外部框架 | `domain/` 文件中 `from fastapi/sqlalchemy` | 🔴 阻止 |
| 跨模块 Repository 实现导入 | `from {{SRC_ROOT}}.modules.X.infrastructure.repositories` | 🟡 警告 |

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

---

## 模板使用检查清单

在使用此模板创建新项目配置时：

- [ ] 替换所有 `{{PLACEHOLDER}}` 占位符
- [ ] 删除不适用的章节和注释
- [ ] 确保 CLAUDE.md 引用此文件
- [ ] 运行架构合规测试验证配置正确
