# 项目配置 - AI Agents Platform Frontend

> **定位**: 本文件是 CLAUDE.md 的补充，包含**项目特定的业务配置**。
> **原则**: 通用规范放 `rules/`，项目特定信息放此处。
> 架构规范详见 [rules/architecture.md](rules/architecture.md)

---

## 项目信息

| 配置项 | 值 |
|--------|-----|
| **项目名称** | ai-agents-platform-frontend |
| **项目描述** | AI Agents Platform - 企业级 AI Agents 平台前端应用 |
| **架构模式** | Feature-Sliced Design (FSD) |
| **Node 版本** | >=18.0.0 |
| **源码根路径** | `src` |

---

## 技术栈补充

> **注意**: 核心技术栈定义在 CLAUDE.md，此处列出版本要求和项目特有选型。

| 类别 | 技术选型 | 版本要求 |
|------|---------|---------|
| **框架** | React | >=18.2.0 |
| **构建** | Vite | >=5.0.0 |
| **样式** | TailwindCSS | >=3.4.0 |
| **服务端状态** | TanStack Query (React Query) | >=5.0.0 |
| **客户端状态** | Zustand | >=4.5.0 |
| **路由** | React Router | >=6.22.0 |
| **表单** | React Hook Form | >=7.50.0 |
| **验证** | Zod | >=3.22.0 |
| **HTTP 客户端** | Axios | >=1.6.0 |
| **UI 组件库** | Radix UI / Shadcn | - |

---

## 功能模块

> **维护提示**: 新增功能时同步更新此表和 `src/features/` 目录。

| 功能 (Feature) | 职责 | 核心组件 |
|----------------|------|---------|
| `auth` | 用户认证与授权 | `LoginForm`, `RegisterForm`, `AuthProvider` |
| `agents` | AI Agent 管理 | `AgentList`, `AgentDetail`, `AgentConfig` |
| `shared` | 共享组件和工具 | `Button`, `Modal`, `useApi` |
<!-- 示例：
| `dashboard` | 仪表盘和数据可视化 | `DashboardLayout`, `MetricsCard` |
| `settings` | 系统设置 | `SettingsForm`, `ProfileEditor` |
-->

---

## 路由配置

> **设计原则**: 路由结构反映业务领域，使用嵌套路由组织相关页面。

| 路径 | 页面 | 功能模块 | 权限 |
|------|------|---------|------|
| `/` | 首页/仪表盘 | `dashboard` | 需登录 |
| `/login` | 登录页 | `auth` | 公开 |
| `/register` | 注册页 | `auth` | 公开 |
| `/agents` | Agent 列表 | `agents` | 需登录 |
| `/agents/:id` | Agent 详情 | `agents` | 需登录 |
| `/settings` | 设置页 | `settings` | 需登录 |

---

## API 端点配置

> **位置约定**: 所有 API 调用放在 `src/shared/api/` 下。

| 端点 | 用途 | 对应后端模块 |
|------|------|-------------|
| `/api/v1/auth/*` | 认证相关 | `auth` |
| `/api/v1/agents/*` | Agent 管理 | `agents` |
| `/api/v1/users/*` | 用户管理 | `auth` |

### API 客户端配置

```typescript
// src/shared/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

---

## 环境变量配置

> **位置**: `.env.example` 模板，`.env.local` 本地配置

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | 后端 API 基础 URL | `http://localhost:8000` |
| `VITE_APP_TITLE` | 应用标题 | `AI Agents Platform` |

---

## 导入路径配置

> **原则**: 使用路径别名简化导入，参考 [rules/architecture.md](rules/architecture.md)

### 路径别名 (tsconfig.json)

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@/shared/*": ["./src/shared/*"],
      "@/features/*": ["./src/features/*"],
      "@/entities/*": ["./src/entities/*"],
      "@/widgets/*": ["./src/widgets/*"],
      "@/pages/*": ["./src/pages/*"]
    }
  }
}
```

### 推荐导入顺序

```typescript
// 1. React 和外部库
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. 共享模块 (从高层到低层)
import { Button, Modal } from '@/shared/ui';
import { useAuth } from '@/shared/hooks';
import { apiClient } from '@/shared/api';

// 3. 功能模块
import { AgentCard } from '@/features/agents';

// 4. 类型导入
import type { Agent } from '@/entities/agent';
```

---

## 架构合规规则

> **详细规则**: 见 [rules/architecture.md](rules/architecture.md) §0.1 依赖合法性速查矩阵

### 违规检测 (Claude 自动检查)

| 违规类型 | 模式 | 严重级别 |
|---------|------|---------|
| 跨 feature 直接导入 | `from '@/features/X'` 在另一个 feature 中 | 🔴 阻止 |
| 低层导入高层 | `shared` 导入 `features` | 🔴 阻止 |
| 业务逻辑在 shared | `shared/` 中包含业务逻辑代码 | 🟡 警告 |
| 组件直接调用 API | 组件中直接使用 `fetch` 或 `axios` | 🟡 警告 |

### 允许的例外

- **Widget 组合**: widgets 可以导入多个 features 的组件进行组合
- **页面组装**: pages 可以导入 widgets、features、entities

---

## PR Review 检查清单

- [ ] 新组件放置在正确的 FSD 层级
- [ ] 导入符合依赖方向规则
- [ ] API 调用通过 React Query hooks
- [ ] 类型定义完整
- [ ] 包含对应的测试文件
