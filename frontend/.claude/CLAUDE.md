# CLAUDE.md - React 前端项目规范

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **注意**: 通用规范（响应语言、项目概述）请参考根目录 [../.claude/CLAUDE.md](../../.claude/CLAUDE.md)

---

## 技术栈

**核心**: React 18+ | TypeScript 5+ | Vite 5+

**样式**: TailwindCSS 3+

**状态管理**: React Query 5+ (服务端状态) | Zustand 4+ (客户端状态)

**测试**: Vitest | Testing Library | Playwright

**工具**: pnpm (包管理) | ESLint | Prettier

---

## 开发命令

### 环境管理 (pnpm)

```bash
# 安装依赖
pnpm install

# 添加生产依赖
pnpm add <package>

# 添加开发依赖
pnpm add -D <package>

# 移除依赖
pnpm remove <package>

# 更新所有依赖
pnpm update
```

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

## 相关规范文档

| 文档 | 内容 |
|------|------|
| [PROJECT_CONFIG.ai-agents-platform.md](PROJECT_CONFIG.ai-agents-platform.md) | 项目特定配置 (功能模块、API 端点) |
| [PROJECT_CONFIG.template.md](PROJECT_CONFIG.template.md) | 项目配置模板 (可复用到其他项目) |
| [rules/architecture.md](rules/architecture.md) | 前端架构规范 (Feature-Sliced Design) |
| [rules/project-structure.md](rules/project-structure.md) | 项目目录结构规范 |
| [rules/component-design.md](rules/component-design.md) | 组件设计规范 |
| [rules/state-management.md](rules/state-management.md) | 状态管理规范 |
| [rules/code-style.md](rules/code-style.md) | 代码风格详细规范 |
| [rules/testing.md](rules/testing.md) | 测试规范详细说明 |
| [rules/security.md](rules/security.md) | 前端安全规范 |
| [rules/performance.md](rules/performance.md) | 性能优化规范 |
| [rules/accessibility.md](rules/accessibility.md) | 无障碍规范 |

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
