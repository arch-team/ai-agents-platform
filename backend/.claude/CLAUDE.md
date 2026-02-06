# CLAUDE.md - Python 后端项目规范

> **职责**: 后端项目的入口规范，定义技术栈、开发命令和核心原则。

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **注意**: 通用规范（响应语言、项目概述）请参考根目录 [../.claude/CLAUDE.md](../../.claude/CLAUDE.md)

---

## 技术栈

**核心**: Python 3.11+ | FastAPI 0.110+ | SQLAlchemy 2.0+ | Pydantic v2 | pytest 8.0+

**工具**: uv (包管理) | Ruff (lint) | MyPy (类型检查)

**云服务**: AWS (SageMaker, S3, DynamoDB) | AWS CDK 2.x

---

## 开发命令

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

# 运行特定模块的测试
uv run pytest tests/modules/auth/

# 运行标记的测试
uv run pytest -m "unit"
uv run pytest -m "integration"
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

详细说明请参考 [rules/sdk-first.md](rules/sdk-first.md)

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

### Docstring 原则

> **类型即文档**: 类型提示 + 好命名 = 自解释代码。Docstring 只写类型无法表达的内容。

详细说明请参考 [rules/code-style.md](rules/code-style.md) §3 Docstring 规范

---

## 项目结构

**项目级目录**: 详见 [rules/project-structure.md](rules/project-structure.md) - 完整目录结构规范

**架构模式**: DDD + Modular Monolith + Clean Architecture

**核心分层**: Domain → Application → Infrastructure → Presentation (依赖方向从外向内)

详细架构规范、模块结构模板、依赖规则请参考 [rules/architecture.md](rules/architecture.md)

---

## 安全规范快速参考

速查表和检测命令详见 [rules/security.md](rules/security.md) Section 0 速查卡片。

---

## API 设计规范

详见 [rules/api-design.md](rules/api-design.md) - RESTful 路由、HTTP 状态码、错误响应格式

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

## PR Review 检查清单

完整检查清单见 [rules/checklist.md](rules/checklist.md)

**预提交一键验证**:
```bash
uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/ && uv run pytest --cov=src --cov-fail-under=85
```
