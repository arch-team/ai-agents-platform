---
name: new-backend-module
description: 按 DDD + Clean Architecture 规范创建新的后端业务模块脚手架
disable-model-invocation: true
---

按照 `backend/.claude/rules/architecture.md` §6 模块结构模板，为新模块生成完整的目录和文件。

## 使用方式

```
/new-backend-module <module_name> <entity_name>
```

示例: `/new-backend-module notifications notification`

## 生成的目录结构

```
backend/src/modules/{module}/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── endpoints.py
│   ├── dependencies.py
│   └── schemas/
│       ├── __init__.py
│       ├── requests.py
│       └── responses.py
├── application/
│   ├── __init__.py
│   ├── dto/
│   │   └── __init__.py
│   ├── interfaces/
│   │   └── __init__.py
│   ├── exceptions/
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
│   ├── services/
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── {entity}_repository.py
│   ├── events.py
│   └── exceptions.py
└── infrastructure/
    ├── __init__.py
    └── persistence/
        ├── __init__.py
        ├── models/
        │   ├── __init__.py
        │   └── {entity}_model.py
        └── repositories/
            ├── __init__.py
            └── {entity}_repository_impl.py
```

同时生成对应的测试目录:

```
backend/tests/modules/{module}/
├── conftest.py
├── unit/
│   ├── domain/
│   │   └── test_{entity}_entity.py
│   └── application/
│       └── test_{entity}_service.py
└── integration/
    ├── test_{entity}_repository.py
    └── test_{module}_endpoints.py
```

## 生成规则

1. **Entity**: 继承 `PydanticEntity`，包含 `ConfigDict(validate_assignment=True)`
2. **Repository 接口**: 继承 `IRepository[{Entity}, int]`，放在 domain/repositories/
3. **Repository 实现**: 继承 `PydanticRepository`，放在 infrastructure/persistence/repositories/
4. **ORM Model**: SQLAlchemy 声明式映射，放在 infrastructure/persistence/models/
5. **Service**: 注入 Repository 接口，包含基础 CRUD 方法
6. **Endpoints**: FastAPI router，路径 `/api/v1/{module}`，POST 返回 201
7. **Schemas**: Pydantic request/response 模型
8. **Events**: 包含 `{Entity}CreatedEvent` 等基础领域事件
9. **Exceptions**: 包含模块专用异常
10. **conftest.py**: 标准三件套 (mock_repo, service, mock_event_bus)
11. **测试**: 基础测试用例骨架 (AAA 模式, pytest.mark 标记)
12. **__init__.py**: 按导出规则只导出公开 API (router, Service, Entity, Events)
13. **所有中文注释**，遵循 `backend/.claude/rules/code-style.md`

## 生成后提醒

- 在 `backend/src/presentation/api/main.py` 中注册新 router
- 在 `backend/src/presentation/api/providers.py` 中注册依赖注入
- 如需数据库迁移，创建 Alembic migration 文件
