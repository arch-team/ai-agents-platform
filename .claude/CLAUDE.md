# CLAUDE.md - Python 后端项目规范

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 响应语言
**所有对话和文档必须（Must）使用中文。**
**除非有特殊说明，请用中文回答。** (Unless otherwise specified, please respond in Chinese.)

### 强制要求

- 所有对话必须使用中文
- 代码注释使用中文
- 文档内容使用中文
- Git 提交信息使用中文

### 例外情况

以下内容保持英文:
- 代码变量名、函数名、类名
- 技术术语 (如 API, SDK, TDD)
- 第三方库/框架名称
- 错误信息和日志 (可选)

---

## 项目概述

AI Agents Platform - 基于 AWS HyperPod 的 ML 训练平台后端服务。

## 技术栈

| 领域 | 技术选型 | 版本要求 |
|------|---------|---------|
| **语言** | Python | 3.11+ |
| **API 框架** | FastAPI | 0.110+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **数据验证** | Pydantic | v2 |
| **测试框架** | pytest | 8.0+ |
| **类型检查** | MyPy | 1.8+ |
| **代码检查** | Ruff | 0.3+ |
| **包管理** | uv | 最新版 |
| **云服务** | AWS (SageMaker, S3, DynamoDB) | - |
| **基础设施** | AWS CDK | 2.x |

---

## 开发命令

### 环境管理 (uv)

```bash
# 安装 uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync

# 添加生产依赖
uv add <package>

# 添加开发依赖
uv add --dev <package>

# 移除依赖
uv remove <package>

# 更新所有依赖
uv lock --upgrade
```

### 代码质量

```bash
# 代码检查 (lint)
uv run ruff check src/

# 代码检查并自动修复
uv run ruff check src/ --fix

# 代码格式化
uv run ruff format src/

# 类型检查
uv run mypy src/

# 一键运行所有检查
uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/
```

### 测试

```bash
# 运行所有测试
uv run pytest

# 运行测试 + 覆盖率报告
uv run pytest --cov=src --cov-report=term-missing

# 遇错停止
uv run pytest -x

# 详细输出
uv run pytest -v

# 运行特定测试文件
uv run pytest tests/unit/test_user.py

# 运行特定测试函数
uv run pytest tests/unit/test_user.py::test_create_user_with_valid_email

# 运行标记的测试
uv run pytest -m "unit"
uv run pytest -m "integration"
uv run pytest -m "e2e"
```

### 服务运行

```bash
# 开发模式运行 API 服务
uv run uvicorn src.presentation.api.main:app --reload --port 8000

# 生产模式运行
uv run uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 核心原则

### SDK-First 原则

**核心原则**：尽可能使用 SDK 简化代码实现，避免重复造轮子。

详细说明请参考 [rules/code-standards.md](rules/code-standards.md)

### TDD 工作流

本项目全面采用测试驱动开发 (TDD)。

**核心循环**:
```
1. 🔴 Red: 先写失败的测试
2. 🟢 Green: 编写最少代码使测试通过
3. 🔄 Refactor: 重构代码，保持测试通过
```

**测试分层策略**:

| 层级 | 后端 | 前端 | 基础设施 |
|------|------|------|---------|
| **Unit** | 实体、值对象、域逻辑 | 组件、Hooks、工具函数 | CDK Construct |
| **Integration** | API 端点、仓库实现 | 页面集成、API 调用 | Stack 集成 |
| **E2E** | HyperPod/S3 集成 | 用户流程 | 部署验证 |

**测试诚信原则**: 切勿为让测试通过而伪造结果。测试失败 = 代码有问题，必须修复代码。

详细说明请参考 [rules/testing.md](rules/testing.md)

---

## 代码风格快速参考

### 类型提示 (必须)

```python
# ✅ 正确
def get_user(user_id: int) -> User | None:
    ...

# ❌ 错误 - 缺少类型
def get_user(user_id):
    ...
```

### 命名规范

| 元素 | 规范 | 示例 |
|------|------|------|
| 函数/变量 | `snake_case` | `get_user_by_id` |
| 类名 | `PascalCase` | `UserRepository` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| 私有成员 | `_leading_underscore` | `_internal_cache` |
| 类型变量 | `PascalCase` + T 后缀 | `EntityT`, `ResponseT` |

### Docstring (Google Style)

```python
def create_user(name: str, email: str) -> User:
    """创建新用户。

    Args:
        name: 用户名称
        email: 用户邮箱

    Returns:
        创建的用户实体

    Raises:
        ValidationError: 邮箱格式无效
    """
```

详细说明请参考 [rules/code-style.md](rules/code-style.md)

---

## 项目结构

**架构模式**: DDD + Modular Monolith + Clean Architecture

**核心分层**: Domain → Application → Infrastructure → Presentation (依赖方向从外向内)

详细架构规范、模块结构模板、依赖规则请参考 [rules/architecture-backend.md](rules/architecture-backend.md)

---

## 安全规范快速参考

速查表和检测命令详见 [rules/security.md](rules/security.md) Section 0 速查卡片。

---

## API 设计规范

### RESTful 路由命名

```python
# ✅ 正确 - 使用复数名词
GET    /api/v1/users          # 获取用户列表
GET    /api/v1/users/{id}     # 获取单个用户
POST   /api/v1/users          # 创建用户
PUT    /api/v1/users/{id}     # 更新用户
DELETE /api/v1/users/{id}     # 删除用户

# ❌ 错误 - 使用动词
POST   /api/v1/createUser
GET    /api/v1/getUserById
```

### 错误响应格式

```python
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    """标准错误响应格式。"""
    code: str           # 错误代码，如 "USER_NOT_FOUND"
    message: str        # 人类可读的错误信息
    details: dict | None = None  # 可选的详细信息
```

### HTTP 状态码使用

| 状态码 | 场景 |
|--------|------|
| 200 | 成功 (GET, PUT) |
| 201 | 创建成功 (POST) |
| 204 | 删除成功 (DELETE) |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 验证错误 |
| 500 | 服务器内部错误 |

---

## 覆盖率要求

| 层级 | 最低覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| Domain | 95% | 100% |
| Application | 90% | 95% |
| Infrastructure | 80% | 85% |
| Presentation | 80% | 85% |
| **整体** | **85%** | **90%** |

---

## 相关规范文档

| 文档 | 内容 |
|------|------|
| [PROJECT_CONFIG.md](PROJECT_CONFIG.md) | 项目特定配置 (模块列表、技术栈、域事件) |
| [rules/architecture-backend.md](rules/architecture-backend.md) | 后端架构规范 (DDD + Modular Monolith + Clean Architecture) |
| [rules/code-standards.md](rules/code-standards.md) | SDK-First 原则详细说明 |
| [rules/code-style.md](rules/code-style.md) | 代码风格详细规范 |
| [rules/testing.md](rules/testing.md) | 测试规范详细说明 |
| [rules/security.md](rules/security.md) | 安全规范详细说明 |

---

## 验证检查清单

在提交代码前，确保通过以下检查：

```bash
# 1. 代码检查通过
uv run ruff check src/

# 2. 格式化检查通过
uv run ruff format --check src/

# 3. 类型检查通过
uv run mypy src/

# 4. 测试通过且覆盖率达标
uv run pytest --cov=src --cov-fail-under=85
```
