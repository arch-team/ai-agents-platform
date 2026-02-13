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

| 层级 | 职责 | 示例 | ✅ 可以 | ❌ 禁止 |
|------|------|------|--------|--------|
| **app** | 应用初始化、路由、全局 Provider | `App.tsx`, `routes.tsx`, `providers.tsx` | Provider、路由、全局样式 | 具体业务实现 |
| **pages** | 页面组件，组装 widgets/features | `LoginPage`, `DashboardPage` | 组合 widgets/features、页面布局 | 业务逻辑 |
| **widgets** | 独立 UI 块，组合多个 features | `Header`, `Sidebar`, `UserMenu` | 组合下层组件、简单状态 | 直接业务逻辑、API 调用 |
| **features** | 业务功能，包含业务逻辑 | `auth/LoginForm`, `agents/AgentList` | 业务逻辑、API 调用、状态管理 | 跨 feature 依赖 |
| **entities** | 业务实体，数据模型和基础 UI | `user/model`, `agent/ui/AgentCard` | 数据模型、基础 UI、类型定义 | 复杂业务逻辑、跨实体依赖 |
| **shared** | 共享工具，无业务逻辑 | `ui/Button`, `api/client`, `lib/utils` | 工具函数、基础 UI、API 客户端 | 任何业务逻辑、业务实体 |

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


---

## 1. 模块导出规则

### 1.1 Public API 原则

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

### 1.2 禁止导出

- 内部工具函数
- 私有组件
- 实现细节

```typescript
// ❌ 错误 - 不应导出内部实现
export { validateEmail } from './lib/validation';
export { useInternalState } from './model/internal';
```

---

## 2. 跨层通信

### 2.1 推荐模式

| 场景 | 推荐方案 | 详细规范 |
|------|---------|---------|
| 组件间数据传递 | Props drilling / Context | - |
| 全局状态 | Zustand store | [state-management.md](state-management.md) §2 |
| 服务端数据 | React Query | [state-management.md](state-management.md) §1 |
| 事件通信 | Custom Events / Zustand | - |
| SSE 流式通信 | 三层架构（见 §2.2） | - |

### 2.2 SSE 流式通信三层架构

| 层级 | 位置 | 职责 | 参考文件 |
|------|------|------|---------|
| **shared 解析器** | `shared/lib/parseSSEStream.ts` | 泛型 `async function*` 生成器，处理 buffer/line splitting/AbortSignal/错误区分 | 全项目唯一 SSE 解析入口 |
| **feature 适配器** | `features/*/lib/sse.ts` | 指定 chunk 类型和 HTTP 方法（POST 发消息 / GET 订阅日志），`yield*` 委托 shared 层 | `execution/lib/sse.ts`, `team-executions/lib/sse.ts` |
| **feature Stream Hook** | `features/*/api/stream.ts` | `useRef<AbortController>` 生命周期管理，通过 Zustand store 管理流式状态，`finally` 块 invalidateQueries 刷新缓存 | `execution/api/stream.ts` |

**关键约定**:
- SSE 不使用 React Query mutation（流式状态由 Zustand 管理）
- token 由调用方传入（避免跨 feature 依赖 auth store）
- 组件卸载时通过 AbortController.abort() 取消连接

