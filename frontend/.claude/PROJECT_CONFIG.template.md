# 项目配置模板 (Project Configuration Template)

<!--
使用说明：
1. 复制此模板到新项目的 .claude/ 目录
2. 替换所有 {{PLACEHOLDER}} 占位符
3. 删除不适用的章节
4. 保持与 CLAUDE.md 的单向引用（CLAUDE.md → PROJECT_CONFIG.md）
-->

> **定位**: 本文件是 CLAUDE.md 的补充，包含**项目特定的业务配置**。
> **原则**: 通用规范放 `rules/`，项目特定信息放此处。
> 架构规范详见 [rules/architecture.md](rules/architecture.md)

---

## 项目信息

<!-- 替换为实际项目信息 -->
| 配置项 | 值 |
|--------|-----|
| **项目名称** | {{PROJECT_NAME}} |
| **项目描述** | {{PROJECT_DESCRIPTION}} |
| **架构模式** | Feature-Sliced Design (FSD) |
| **Node 版本** | >=18.0.0 |
| **源码根路径** | `src` |

---

## 技术栈补充

> **注意**: 核心技术栈定义在 CLAUDE.md，此处仅列出**项目特有**的技术选型。

| 类别 | 技术选型 | 用途说明 |
|------|---------|---------|
| **UI 组件库** | {{UI_LIBRARY}} | {{UI_PURPOSE}} |
| **图表库** | {{CHART_LIBRARY}} | {{CHART_PURPOSE}} |
<!-- 添加其他项目特有技术 -->

---

## 功能模块

> **维护提示**: 新增功能时同步更新此表和 `src/features/` 目录。

| 功能 (Feature) | 职责 | 核心组件 |
|----------------|------|---------|
| `auth` | 用户认证与授权 | `LoginForm`, `AuthProvider` |
| `{{FEATURE_1}}` | {{FEATURE_1_DESC}} | `{{COMPONENT_1}}` |
| `{{FEATURE_2}}` | {{FEATURE_2_DESC}} | `{{COMPONENT_2}}` |
| `shared` | 共享组件和工具 (必须保留) | `Button`, `Modal` |

---

## 路由配置

> **设计原则**: 路由结构反映业务领域，使用嵌套路由组织相关页面。

| 路径 | 页面 | 功能模块 | 权限 |
|------|------|---------|------|
| `/` | 首页 | `{{MODULE}}` | 需登录 |
| `/login` | 登录页 | `auth` | 公开 |
| `/{{ROUTE_1}}` | {{PAGE_1}} | `{{FEATURE}}` | {{PERMISSION}} |

---

## API 端点配置

> **位置约定**: 所有 API 调用放在 `src/shared/api/` 下。

| 端点 | 用途 | 对应后端模块 |
|------|------|-------------|
| `/api/v1/auth/*` | 认证相关 | `auth` |
| `/api/v1/{{RESOURCE}}/*` | {{PURPOSE}} | `{{MODULE}}` |

---

## 环境变量配置

> **位置**: `.env.example` 模板，`.env.local` 本地配置

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | 后端 API 基础 URL | `http://localhost:8000` |
| `VITE_{{VAR_NAME}}` | {{VAR_DESC}} | {{VAR_EXAMPLE}} |

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

---

## 架构合规规则

> **详细规则**: 见 [rules/architecture.md](rules/architecture.md) §0.1 依赖合法性速查矩阵

### 违规检测 (Claude 自动检查)

| 违规类型 | 模式 | 严重级别 |
|---------|------|---------|
| 跨 feature 直接导入 | `from '@/features/X'` 在另一个 feature 中 | 🔴 阻止 |
| 低层导入高层 | `shared` 导入 `features` | 🔴 阻止 |
| 业务逻辑在 shared | `shared/` 中包含业务逻辑代码 | 🟡 警告 |

### 允许的例外

- **Widget 组合**: widgets 可以导入多个 features 的组件进行组合
- **页面组装**: pages 可以导入 widgets、features、entities

---

## 模板使用检查清单

在使用此模板创建新项目配置时：

- [ ] 替换所有 `{{PLACEHOLDER}}` 占位符
- [ ] 删除不适用的章节和注释
- [ ] 确保 CLAUDE.md 引用此文件
- [ ] 配置 tsconfig.json 路径别名
