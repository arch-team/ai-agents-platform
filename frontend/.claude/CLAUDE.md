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

### 组件设计原则

**核心原则**：单一职责 + 组合优于继承 + 类型安全。

详细说明请参考 [rules/component-design.md](rules/component-design.md)

### TDD 工作流

本项目全面采用测试驱动开发 (TDD)。

**核心循环**:
```
1. 🔴 Red: 先写失败的测试
2. 🟢 Green: 编写最少代码使测试通过
3. 🔄 Refactor: 重构代码，保持测试通过
```

**测试分层策略**:

| 层级 | 覆盖内容 | 工具 |
|------|---------|------|
| **Unit** | Hooks、工具函数、组件 | Vitest + Testing Library |
| **Integration** | 页面集成、API 调用 | Vitest + MSW |
| **E2E** | 用户流程、关键路径 | Playwright |

**测试诚信原则**: 切勿为让测试通过而伪造结果。测试失败 = 代码有问题，必须修复代码。

详细说明请参考 [rules/testing.md](rules/testing.md)

---

## 代码风格快速参考

### 类型提示 (必须)

```typescript
// ✅ 正确 - 使用接口定义 Props
interface ButtonProps {
  variant: 'primary' | 'secondary';
  onClick: () => void;
  children: React.ReactNode;
}

// ❌ 错误 - 缺少类型
const Button = ({ variant, onClick, children }) => { ... }
```

### 命名规范

| 元素 | 规范 | 示例 |
|------|------|------|
| 组件 | `PascalCase` | `UserProfile`, `LoginForm` |
| 函数/变量 | `camelCase` | `getUserData`, `isLoading` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| CSS 类 | `kebab-case` | `user-profile`, `login-form` |
| 类型/接口 | `PascalCase` | `UserData`, `ApiResponse` |
| Hooks | `use` 前缀 + `camelCase` | `useAuth`, `useFetch` |

### 组件文件命名

```
{ComponentName}/
├── index.ts              # 导出入口
├── {ComponentName}.tsx   # 组件实现
├── {ComponentName}.test.tsx  # 单元测试
├── {ComponentName}.types.ts  # 类型定义 (可选)
└── {ComponentName}.module.css  # 样式 (可选)
```

详细说明请参考 [rules/code-style.md](rules/code-style.md)

---

## 项目结构

**架构模式**: Feature-Sliced Design (FSD)

**核心分层**: app → pages → widgets → features → entities → shared

详细架构规范、目录结构、依赖规则请参考 [rules/architecture.md](rules/architecture.md)

**项目目录结构**: 详见 [rules/project-structure.md](rules/project-structure.md)

---

## 状态管理快速参考

**决策流程**:
```
数据来自服务端 API？ ──是──► React Query (TanStack Query)
       │
      否
       ↓
需要跨组件共享？ ──是──► Zustand Store
       │
      否
       ↓
组件本地状态 → useState / useReducer
```

详见 [rules/state-management.md](rules/state-management.md)

---

## 安全规范快速参考

速查表和检测命令详见 [rules/security.md](rules/security.md)

---

## 覆盖率要求

| 层级 | 最低覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| Hooks | 90% | 95% |
| Components | 80% | 85% |
| Utils | 95% | 100% |
| **整体** | **80%** | **85%** |

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
