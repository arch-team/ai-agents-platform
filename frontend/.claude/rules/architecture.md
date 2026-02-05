> **职责**: FSD 架构规范的单一真实源 - 分层规则、依赖矩阵、Slice 结构模板

# 前端架构规范 (Frontend Architecture Standards)

> **架构模式**: Feature-Sliced Design (FSD)
> **适用范围**: React + TypeScript 前端项目

<!-- CLAUDE 占位符说明:
  {Feature}    → 功能名称 PascalCase，如 Auth, Agents, Dashboard
  {feature}    → 功能名称 kebab-case，如 auth, agents, dashboard
  {Entity}     → 实体名称 PascalCase，如 User, Agent
  {entity}     → 实体名称 kebab-case，如 user, agent
  {Component}  → 组件名称 PascalCase，如 LoginForm, AgentCard
  {Widget}     → 组件组合 PascalCase，如 Header, Sidebar
-->

---

## 0. 速查卡片

> Claude 生成代码时优先查阅此章节

### 0.1 FSD 分层依赖矩阵

| 从 ↓ 导入 → | shared | entities | features | widgets | pages | app |
|-------------|:------:|:--------:|:--------:|:-------:|:-----:|:---:|
| **app** | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| **pages** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **widgets** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **features** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **entities** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **shared** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**图例**: ✅ 允许 | ❌ 禁止

**核心规则**: 只能向下依赖，不能向上或平级依赖

### 0.2 层级职责速查

| 层级 | 职责 | 示例 |
|------|------|------|
| **app** | 应用初始化、路由、全局 Provider | `App.tsx`, `routes.tsx`, `providers.tsx` |
| **pages** | 页面组件，组装 widgets/features | `LoginPage`, `DashboardPage` |
| **widgets** | 独立 UI 块，组合多个 features | `Header`, `Sidebar`, `UserMenu` |
| **features** | 业务功能，包含业务逻辑 | `auth/LoginForm`, `agents/AgentList` |
| **entities** | 业务实体，数据模型和基础 UI | `user/model`, `agent/ui/AgentCard` |
| **shared** | 共享工具，无业务逻辑 | `ui/Button`, `api/client`, `lib/utils` |

### 0.3 Slice 结构模板

```
{layer}/{slice}/
├── index.ts              # 公开 API 导出
├── api/                  # API 调用 (features/entities 专用)
│   └── queries.ts
├── model/                # 状态管理
│   ├── store.ts          # Zustand store
│   └── types.ts          # 类型定义
├── ui/                   # UI 组件
│   ├── {Component}.tsx
│   └── {Component}.test.tsx
└── lib/                  # 工具函数
    └── utils.ts
```

### 0.4 PR Review 检查清单

**分层规则**:
- [ ] 新文件放置在正确的 FSD 层级
- [ ] 依赖方向正确（只向下依赖）
- [ ] 没有跨 feature 的直接导入
- [ ] shared 层没有业务逻辑

**Slice 结构**:
- [ ] 每个 slice 有 `index.ts` 统一导出
- [ ] API 调用在 `api/` 目录，使用 React Query
- [ ] 状态管理在 `model/` 目录
- [ ] UI 组件在 `ui/` 目录

**类型安全**:
- [ ] 所有导出有明确类型
- [ ] Props 使用 interface 定义
- [ ] 避免 `any` 类型

---

## 1. 分层规则

### 1.1 各层职责与约束

| 层级 | 职责 | ✅ 可以 | ❌ 禁止 |
|------|------|--------|--------|
| **shared** | 无业务逻辑的可复用代码 | 工具函数、基础 UI、API 客户端 | 任何业务逻辑、业务实体 |
| **entities** | 业务实体及其基础表示 | 数据模型、基础 UI、类型定义 | 复杂业务逻辑、跨实体依赖 |
| **features** | 具体业务功能 | 业务逻辑、API 调用、状态管理 | 跨 feature 依赖 |
| **widgets** | 组合多个 features/entities | 组合下层组件、简单状态 | 直接业务逻辑、API 调用 |
| **pages** | 页面组装，连接路由 | 组合 widgets/features、页面布局 | 业务逻辑 |
| **app** | 应用初始化、全局配置 | Provider、路由、全局样式 | 具体业务实现 |

> **目录结构示例**: 详见 [project-structure.md](project-structure.md)

---

## 2. 模块导出规则

### 2.1 Public API 原则

每个 slice 必须有 `index.ts` 定义公开 API：

```typescript
// features/auth/index.ts
// UI 组件
export { LoginForm } from './ui/LoginForm';
export { RegisterForm } from './ui/RegisterForm';

// Hooks
export { useAuth } from './model/store';
export { useLogin, useLogout } from './api/queries';

// 类型
export type { LoginCredentials, AuthState } from './model/types';
```

### 2.2 禁止导出

- 内部工具函数
- 私有组件
- 实现细节

```typescript
// ❌ 错误 - 不应导出内部实现
export { validateEmail } from './lib/validation';
export { useInternalState } from './model/internal';
```

---

## 3. 跨层通信

### 3.1 推荐模式

| 场景 | 推荐方案 | 详细规范 |
|------|---------|---------|
| 组件间数据传递 | Props drilling / Context | - |
| 全局状态 | Zustand store | [state-management.md](state-management.md) §2 |
| 服务端数据 | React Query | [state-management.md](state-management.md) §1 |
| 事件通信 | Custom Events / Zustand | - |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [project-structure.md](project-structure.md) | 目录结构详解 |
| [component-design.md](component-design.md) | 组件设计规范、组件模板 |
| [state-management.md](state-management.md) | 状态管理详细规范 |
| [testing.md](testing.md) | 测试规范 |
