> **职责**: 目录结构规范 - 物理目录结构和配置文件速查

# 项目目录结构规范 (Project Structure)

---

## 0. 速查卡片

> Monorepo 结构概览请参考 [根级 common.md](../../../.claude/rules/common.md#monorepo-结构概览)

### 前端目录结构 ← 当前位置

```
frontend/                       # 前端项目根目录
├── .claude/                    # Claude Code 上下文 (规范文档)
│   ├── CLAUDE.md               # 前端入口
│   ├── project-config*.md
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

> 各层级的职责、依赖规则、Slice 结构模板详见 [architecture.md](architecture.md) §0-2
>
> 本节仅展示目录树结构示例。

### src/ 目录结构示例

```
src/
├── app/                        # 应用层 → 见 architecture.md §2.6
├── pages/                      # 页面层 → 见 architecture.md §2.5
├── widgets/                    # 组件层 → 见 architecture.md §2.4
├── features/                   # 功能层 → 见 architecture.md §2.3
├── entities/                   # 实体层 → 见 architecture.md §2.2
└── shared/                     # 共享层 → 见 architecture.md §2.1
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

完整检查清单见 [checklist.md](checklist.md) §项目结构
