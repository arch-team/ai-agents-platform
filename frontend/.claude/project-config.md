> **职责**: 项目特定配置 - 功能模块、路由、API 端点、环境变量（业务配置单一真实源）

# 项目配置 - AI Agents Platform Frontend

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

## 技术栈版本要求

> **技术栈版本**: 详见 [rules/tech-stack.md](rules/tech-stack.md) (单一真实源)
>
> 如需项目特定的版本约束，请在 `package.json` 的 `engines` 或 `peerDependencies` 中定义。

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

> 路径别名和导入规范详见 [rules/architecture.md](rules/architecture.md) §3 和 [rules/code-style.md](rules/code-style.md) §3

---

## 架构合规规则

> 依赖规则、违规检测、允许的例外详见 [rules/architecture.md](rules/architecture.md) §0.1 依赖合法性速查矩阵

---

## PR Review 检查清单

- [ ] 新组件放置在正确的 FSD 层级
- [ ] 导入符合依赖方向规则
- [ ] API 调用通过 React Query hooks
- [ ] 类型定义完整
- [ ] 包含对应的测试文件
