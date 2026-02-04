# 前端架构规范 (Frontend Architecture Standards)

> **版本**: 1.0
> **架构模式**: Feature-Sliced Design (FSD)
> **适用范围**: React + TypeScript 前端项目

本文档是前端项目的**核心架构规范单一真实源 (Single Source of Truth)**。

<!-- CLAUDE: 项目特定配置请参考 PROJECT_CONFIG.ai-agents-platform.md -->

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

## 1. Feature-Sliced Design 概述

### 1.1 为什么选择 FSD

| 优势 | 说明 |
|------|------|
| **可预测性** | 明确的分层规则，代码位置一目了然 |
| **可扩展性** | 功能隔离，新增功能不影响其他部分 |
| **可维护性** | 职责清晰，便于团队协作和代码审查 |
| **可测试性** | 模块独立，便于单元测试和集成测试 |

### 1.2 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                         app (应用层)                         │
│                    初始化、路由、全局配置                      │
├─────────────────────────────────────────────────────────────┤
│                        pages (页面层)                        │
│                      页面组件，组装层                         │
├─────────────────────────────────────────────────────────────┤
│                       widgets (组件层)                       │
│                   独立 UI 块，组合 features                   │
├─────────────────────────────────────────────────────────────┤
│                       features (功能层)                      │
│                   业务功能，核心业务逻辑                       │
├─────────────────────────────────────────────────────────────┤
│                       entities (实体层)                      │
│                    业务实体，数据模型                         │
├─────────────────────────────────────────────────────────────┤
│                        shared (共享层)                       │
│                   无业务逻辑的共享代码                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 分层详解

### 2.1 shared (共享层)

**职责**: 提供无业务逻辑的可复用代码

**禁止**: 任何业务逻辑、业务实体、业务规则

```
shared/
├── api/                  # API 客户端配置
│   ├── client.ts         # Axios 实例
│   └── types.ts          # 通用 API 类型
├── config/               # 应用配置
│   └── env.ts
├── hooks/                # 通用 Hooks
│   ├── useDebounce.ts
│   └── useLocalStorage.ts
├── lib/                  # 工具函数
│   ├── utils.ts
│   └── date.ts
├── ui/                   # 基础 UI 组件
│   ├── Button/
│   ├── Modal/
│   └── Input/
└── types/                # 全局类型定义
    └── common.ts
```

### 2.2 entities (实体层)

**职责**: 定义业务实体及其基础表示

**可以**: 定义数据模型、基础 UI 组件、类型

**禁止**: 复杂业务逻辑、API 调用（仅基础查询）

```
entities/
├── user/
│   ├── index.ts          # 导出 User 类型和 UserCard
│   ├── model/
│   │   └── types.ts      # User 类型定义
│   └── ui/
│       └── UserAvatar.tsx
├── agent/
│   ├── index.ts
│   ├── model/
│   │   └── types.ts      # Agent 类型定义
│   └── ui/
│       └── AgentCard.tsx
└── session/
    └── ...
```

### 2.3 features (功能层)

**职责**: 实现具体业务功能

**可以**: 业务逻辑、API 调用、状态管理、复杂交互

**禁止**: 跨 feature 依赖

```
features/
├── auth/
│   ├── index.ts          # 导出 LoginForm, useAuth, etc.
│   ├── api/
│   │   └── queries.ts    # React Query hooks
│   ├── model/
│   │   ├── store.ts      # Zustand auth store
│   │   └── types.ts
│   └── ui/
│       ├── LoginForm.tsx
│       └── RegisterForm.tsx
├── agents/
│   ├── index.ts
│   ├── api/
│   │   └── queries.ts
│   ├── model/
│   │   └── types.ts
│   └── ui/
│       ├── AgentList.tsx
│       └── AgentConfig.tsx
└── ...
```

### 2.4 widgets (组件层)

**职责**: 组合多个 features/entities 形成独立 UI 块

**可以**: 组合下层组件、简单状态管理

**禁止**: 直接业务逻辑、API 调用

```
widgets/
├── header/
│   ├── index.ts
│   └── ui/
│       └── Header.tsx    # 组合 UserMenu + Navigation
├── sidebar/
│   ├── index.ts
│   └── ui/
│       └── Sidebar.tsx
└── user-menu/
    ├── index.ts
    └── ui/
        └── UserMenu.tsx  # 组合 UserAvatar + Dropdown
```

### 2.5 pages (页面层)

**职责**: 组装页面，连接路由

**可以**: 组合 widgets/features、页面级布局

```
pages/
├── login/
│   ├── index.ts
│   └── ui/
│       └── LoginPage.tsx
├── dashboard/
│   ├── index.ts
│   └── ui/
│       └── DashboardPage.tsx
└── agents/
    ├── index.ts
    └── ui/
        ├── AgentsPage.tsx
        └── AgentDetailPage.tsx
```

### 2.6 app (应用层)

**职责**: 应用初始化、全局配置

```
app/
├── index.tsx             # 应用入口
├── App.tsx               # 根组件
├── providers/            # 全局 Provider
│   ├── index.tsx
│   ├── QueryProvider.tsx
│   └── AuthProvider.tsx
├── routes/               # 路由配置
│   └── index.tsx
└── styles/               # 全局样式
    └── global.css
```

---

## 3. 模块导出规则

### 3.1 Public API 原则

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

### 3.2 禁止导出

- 内部工具函数
- 私有组件
- 实现细节

```typescript
// ❌ 错误 - 不应导出内部实现
export { validateEmail } from './lib/validation';
export { useInternalState } from './model/internal';
```

---

## 4. 跨层通信

### 4.1 推荐模式

| 场景 | 推荐方案 |
|------|---------|
| 组件间数据传递 | Props drilling / Context |
| 全局状态 | Zustand store |
| 服务端数据 | React Query |
| 事件通信 | Custom Events / Zustand |

### 4.2 React Query 集成

```typescript
// features/agents/api/queries.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/shared/api';
import type { Agent } from '@/entities/agent';

export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  detail: (id: string) => [...agentKeys.all, 'detail', id] as const,
};

export function useAgents() {
  return useQuery({
    queryKey: agentKeys.lists(),
    queryFn: () => apiClient.get<Agent[]>('/api/v1/agents').then(r => r.data),
  });
}

export function useAgent(id: string) {
  return useQuery({
    queryKey: agentKeys.detail(id),
    queryFn: () => apiClient.get<Agent>(`/api/v1/agents/${id}`).then(r => r.data),
    enabled: !!id,
  });
}
```

### 4.3 Zustand Store

```typescript
// features/auth/model/store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/entities/user';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    { name: 'auth-storage' }
  )
);

// 导出 selector hooks
export const useAuth = () => useAuthStore((state) => ({
  user: state.user,
  isAuthenticated: state.isAuthenticated,
}));
```

---

## 5. 常见模式

### 5.1 Feature 组件模板

```typescript
// features/{feature}/ui/{Component}.tsx
import { useState } from 'react';
import { Button } from '@/shared/ui';
import { use{Feature}Mutation } from '../api/queries';
import type { {Feature}Props } from '../model/types';

interface {Component}Props {
  onSuccess?: () => void;
}

export function {Component}({ onSuccess }: {Component}Props) {
  const mutation = use{Feature}Mutation();

  const handleSubmit = async () => {
    await mutation.mutateAsync(data);
    onSuccess?.();
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* ... */}
      <Button type="submit" loading={mutation.isPending}>
        提交
      </Button>
    </form>
  );
}
```

### 5.2 Entity UI 模板

```typescript
// entities/{entity}/ui/{Entity}Card.tsx
import type { {Entity} } from '../model/types';

interface {Entity}CardProps {
  {entity}: {Entity};
  onClick?: () => void;
}

export function {Entity}Card({ {entity}, onClick }: {Entity}CardProps) {
  return (
    <div onClick={onClick} className="...">
      <h3>{({entity} as any).name}</h3>
      {/* 仅展示逻辑，无业务逻辑 */}
    </div>
  );
}
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `PROJECT_CONFIG.ai-agents-platform.md` | 项目特定配置 (功能模块、路由配置) |
| `CLAUDE.md` | TDD 工作流、命令、代码风格 |
| `rules/component-design.md` | 组件设计规范 |
| `rules/state-management.md` | 状态管理详细规范 |
| `rules/testing.md` | 测试规范 |
