# 技术约定

> AI Agents Platform 的技术约定 — 仅记录非显而易见的规则

## 技术栈

### Monorepo 结构
- 后端: Python 3.12 + FastAPI + SQLAlchemy 2.0 + MySQL 8.0
- 前端: React 19 + TypeScript + Vite + TailwindCSS 4
- 基础设施: AWS CDK + TypeScript

### 包管理
- backend: `uv`（禁止 pip/poetry）
- frontend/infra: `pnpm`（禁止 npm/yarn）

### 代码质量工具
- backend: ruff (lint+format) + mypy (type check) + pytest
- frontend: ESLint 9 + Prettier + TypeScript + Vitest + Playwright
- infra: ESLint + Prettier + TypeScript + Jest + CDK Nag

## 编码规范

### 命名规范
- backend: `snake_case` (函数/变量), `PascalCase` (类)
- frontend: `camelCase` (函数/变量), `PascalCase` (组件/类型)
- infra: `camelCase` (函数/变量), `PascalCase` (类/Construct)

### 架构模式
- backend: DDD + Modular Monolith + Clean Architecture
- frontend: Feature-Sliced Design (FSD)
- infra: CDK Construct 分层 (L1→L2→L3)

## 开发流程

- **分支策略**: trunk-based（main + feature 分支）
- **Git 提交格式**: `<类型>(<范围>): <描述>`（类型: feat/fix/docs/refactor/test/chore，范围: backend/frontend/infra/*）

## 项目约定

### SDK-First 原则
优先使用官方 SDK 和成熟第三方库，避免重复造轮子（详见各子项目 rules/sdk-first.md）

### TDD 工作流
所有子项目采用测试驱动开发：先写测试 → 实现代码 → 重构

### 覆盖率要求
- backend: 整体 ≥85%（Domain ≥95%, Application ≥90%）
- frontend: 整体 ≥80%（Hooks ≥90%, Components ≥80%）
- infra: 整体 ≥85%（Constructs ≥90%）

## 架构约束

### 模块间通信
- backend: EventBus (异步) 或 shared/interfaces (同步)，禁止跨模块直接依赖
- frontend: 仅向下依赖（app → pages → widgets → features → entities → shared）

### 敏感数据
- backend: 使用 AWS Secrets Manager，禁止硬编码
- frontend: Token 存内存或 httpOnly Cookie，禁止 localStorage

（随开发自然积累 — 发现重要约束时由 Claude 或用户添加）
