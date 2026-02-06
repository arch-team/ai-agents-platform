> **职责**: 前端项目入口文档 - 技术栈概览、开发命令、规范导航

# CLAUDE.md - React 前端项目规范

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **注意**: 通用规范（响应语言、项目概述）请参考根目录 [../.claude/CLAUDE.md](../../.claude/CLAUDE.md)

---

## 技术栈

> **详细技术栈规范**: 参考 [rules/tech-stack.md](rules/tech-stack.md) (单一真实源)

**概览**: React 18+ | TypeScript 5+ | Vite 5+ | TailwindCSS | React Query | Zustand

---

## 开发命令

### 代码质量

```bash
# 代码检查 (lint)
pnpm lint

# 代码检查并自动修复
pnpm lint --fix

# 格式化检查
pnpm format:check

# 格式化代码
pnpm format

# 类型检查
pnpm typecheck

# 一键运行所有检查
pnpm lint && pnpm format:check && pnpm typecheck
```

### 测试

```bash
# 运行所有测试
pnpm test

# 运行测试 + 覆盖率报告
pnpm test:coverage

# 运行 UI 模式
pnpm test:ui

# 运行 E2E 测试 (Playwright)
pnpm test:e2e

# 运行特定测试文件
pnpm test src/features/auth/
```

### 开发服务

```bash
# 开发模式运行
pnpm dev

# 构建生产版本
pnpm build

# 预览生产构建
pnpm preview
```

---

## 核心原则

| 原则 | 说明 | 详细规范 |
|------|------|---------|
| **组件设计** | 单一职责 + 组合优于继承 + 类型安全 | [component-design.md](rules/component-design.md) |
| **TDD 工作流** | 红-绿-重构循环，测试诚信原则 | [testing.md](rules/testing.md) |
| **状态管理** | 服务端→React Query，客户端→Zustand | [state-management.md](rules/state-management.md) |
| **代码风格** | 命名规范、TypeScript、导入排序 | [code-style.md](rules/code-style.md) |

---

## 项目结构

**架构模式**: Feature-Sliced Design (FSD)

**核心分层**: app → pages → widgets → features → entities → shared

详细架构规范、目录结构、依赖规则请参考 [rules/architecture.md](rules/architecture.md)

**项目目录结构**: 详见 [rules/project-structure.md](rules/project-structure.md)

---

## 验证检查清单

在提交代码前，确保通过以下检查：

```bash
# 1. 代码检查通过
pnpm lint

# 2. 格式化检查通过
pnpm format:check

# 3. 类型检查通过
pnpm typecheck

# 4. 测试通过且覆盖率达标
pnpm test:coverage
```
