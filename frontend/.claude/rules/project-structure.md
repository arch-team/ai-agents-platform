# 项目目录结构规范 (Project Structure)

> Claude 初始化或检查项目结构时优先查阅此文档

---

## 0. 速查卡片

> Monorepo 结构概览请参考 [根级 common.md](../../../.claude/rules/common.md#monorepo-结构概览)

### 前端目录结构 ← 当前位置

```
frontend/                       # 前端项目根目录
├── .claude/                    # Claude Code 上下文 (规范文档)
│   ├── CLAUDE.md               # 前端入口
│   ├── PROJECT_CONFIG.*.md
│   └── rules/                  # 前端专用规则
├── public/                     # 静态资源
│   └── favicon.ico
├── src/                        # 源代码 (FSD 结构)
│   ├── app/                    # 应用层
│   │   ├── App.tsx
│   │   ├── providers/
│   │   ├── routes/
│   │   └── styles/
│   ├── pages/                  # 页面层
│   ├── widgets/                # 组件层
│   ├── features/               # 功能层
│   ├── entities/               # 实体层
│   └── shared/                 # 共享层
│       ├── api/
│       ├── config/
│       ├── hooks/
│       ├── lib/
│       ├── types/
│       └── ui/
├── tests/                      # E2E 测试 (Playwright)
│   ├── e2e/
│   └── fixtures/
├── .env.example                # 环境变量模板
├── .eslintrc.cjs               # ESLint 配置
├── .prettierrc                 # Prettier 配置
├── index.html                  # HTML 入口
├── package.json                # 项目配置
├── pnpm-lock.yaml              # 依赖锁定
├── postcss.config.js           # PostCSS 配置
├── tailwind.config.js          # TailwindCSS 配置
├── tsconfig.json               # TypeScript 配置
├── tsconfig.node.json          # Node TypeScript 配置
├── vite.config.ts              # Vite 配置
└── README.md                   # 前端说明
```

### 配置文件速查

| 文件 | 用途 | 必须 |
|------|------|:----:|
| `package.json` | 项目和脚本配置 | ✅ |
| `tsconfig.json` | TypeScript 配置 | ✅ |
| `vite.config.ts` | Vite 构建配置 | ✅ |
| `.env.example` | 环境变量模板 | ✅ |
| `tailwind.config.js` | TailwindCSS 配置 | ✅ |
| `.eslintrc.cjs` | ESLint 配置 | ✅ |
| `.prettierrc` | Prettier 配置 | ✅ |
| `README.md` | 项目说明 | ✅ |
| `playwright.config.ts` | E2E 测试配置 | 推荐 |

### 禁止事项

| 规则 | 说明 |
|------|------|
| ❌ 根目录放组件 | 所有组件必须在 `src/` 对应层级下 |
| ❌ 测试散落源码目录 | 单元测试与组件同目录，E2E 在 `tests/` |
| ❌ 配置文件散落各处 | 配置统一在根目录 |
| ❌ 未声明的环境变量 | 所有变量必须在 `.env.example` 中声明 |

---

## 1. FSD 层级详解

### src/ 目录结构

```
src/
├── app/                        # 应用初始化
│   ├── index.tsx               # 入口点
│   ├── App.tsx                 # 根组件
│   ├── providers/              # 全局 Provider
│   │   ├── index.tsx           # Provider 组合
│   │   ├── QueryProvider.tsx   # React Query
│   │   ├── AuthProvider.tsx    # 认证上下文
│   │   └── ThemeProvider.tsx   # 主题上下文
│   ├── routes/                 # 路由配置
│   │   ├── index.tsx           # 路由定义
│   │   ├── PrivateRoute.tsx    # 私有路由守卫
│   │   └── PublicRoute.tsx     # 公开路由守卫
│   └── styles/                 # 全局样式
│       └── global.css
│
├── pages/                      # 页面组件
│   ├── login/
│   │   ├── index.ts
│   │   └── ui/LoginPage.tsx
│   ├── dashboard/
│   │   ├── index.ts
│   │   └── ui/DashboardPage.tsx
│   └── not-found/
│       ├── index.ts
│       └── ui/NotFoundPage.tsx
│
├── widgets/                    # 复合组件
│   ├── header/
│   │   ├── index.ts
│   │   └── ui/Header.tsx
│   ├── sidebar/
│   │   ├── index.ts
│   │   └── ui/Sidebar.tsx
│   └── layout/
│       ├── index.ts
│       └── ui/MainLayout.tsx
│
├── features/                   # 业务功能
│   ├── auth/
│   │   ├── index.ts            # 公开 API
│   │   ├── api/queries.ts      # React Query hooks
│   │   ├── model/
│   │   │   ├── store.ts        # Zustand store
│   │   │   └── types.ts        # 类型定义
│   │   └── ui/
│   │       ├── LoginForm.tsx
│   │       └── LoginForm.test.tsx
│   └── agents/
│       ├── index.ts
│       ├── api/queries.ts
│       ├── model/types.ts
│       └── ui/
│           ├── AgentList.tsx
│           └── AgentConfig.tsx
│
├── entities/                   # 业务实体
│   ├── user/
│   │   ├── index.ts
│   │   ├── model/types.ts
│   │   └── ui/UserAvatar.tsx
│   └── agent/
│       ├── index.ts
│       ├── model/types.ts
│       └── ui/AgentCard.tsx
│
└── shared/                     # 共享代码
    ├── api/
    │   ├── client.ts           # Axios 实例
    │   └── types.ts            # API 通用类型
    ├── config/
    │   └── env.ts              # 环境配置
    ├── hooks/
    │   ├── useDebounce.ts
    │   └── useLocalStorage.ts
    ├── lib/
    │   ├── utils.ts            # 工具函数
    │   └── cn.ts               # classNames 工具
    ├── types/
    │   └── common.ts           # 通用类型
    └── ui/                     # 基础 UI 组件
        ├── Button/
        │   ├── index.ts
        │   ├── Button.tsx
        │   └── Button.test.tsx
        ├── Modal/
        ├── Input/
        └── index.ts            # 统一导出
```

---

## 2. 跨文档引用

| 内容 | 参考文档 |
|------|---------|
| FSD 分层规则和依赖矩阵 | [architecture.md](architecture.md) §0.1 |
| 组件设计模式 | [component-design.md](component-design.md) |
| 测试目录结构 | [testing.md](testing.md) §1 |
| 根级通用规范 | [../../.claude/CLAUDE.md](../../../.claude/CLAUDE.md) |

---

## 3. 新项目初始化检查清单

### 目录
- [ ] `src/app/` 包含 App.tsx、providers/、routes/
- [ ] `src/shared/` 包含 api/、ui/、hooks/、lib/
- [ ] `src/features/` 和 `src/entities/` 已创建
- [ ] `.claude/CLAUDE.md` 已配置

### 配置文件
- [ ] `package.json` 包含所有必要脚本
- [ ] `tsconfig.json` 配置路径别名
- [ ] `vite.config.ts` 配置路径别名
- [ ] `.env.example` 列出所有环境变量
- [ ] `tailwind.config.js` 已配置
- [ ] `README.md` 包含项目说明

### 代码质量
- [ ] `.eslintrc.cjs` 配置 React + TypeScript 规则
- [ ] `.prettierrc` 配置格式化规则
- [ ] `vitest.config.ts` 配置测试

---

## PR Review 检查清单

- [ ] 新文件放置在正确的 FSD 层级
- [ ] 组件与测试文件同目录
- [ ] 新 slice 有 `index.ts` 导出
- [ ] 无临时文件被提交
- [ ] 环境变量已在 `.env.example` 声明
