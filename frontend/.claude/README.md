# Claude Code 上下文管理

本文档用于说明 ./frontend React 前端项目的Claude Code的上下文配置文件,不直接作用该项目的规范

---

## 目录结构

```
.claude/
├── README.md                              # 本文件 - 目录说明
├── CLAUDE.md                              # 项目主规范 (入口)
├── PROJECT_CONFIG.ai-agents-platform.md   # 项目特定配置
├── PROJECT_CONFIG.template.md             # 项目配置模板
└── rules/                                 # 专题规范文档
    ├── architecture.md                    # 架构规范 (FSD) ★核心
    ├── project-structure.md               # 项目目录结构规范
    ├── component-design.md                # 组件设计规范
    ├── state-management.md                # 状态管理规范
    ├── code-style.md                      # 代码风格规范
    ├── testing.md                         # 测试规范 (TDD)
    ├── security.md                        # 前端安全规范
    ├── performance.md                     # 性能优化规范
    └── accessibility.md                   # 无障碍规范
```

---

## 快速开始

### 开发者入门

1. **阅读入口**: 从 `CLAUDE.md` 开始，了解项目概况和核心原则
2. **查阅配置**: 参考 `PROJECT_CONFIG.ai-agents-platform.md` 了解功能模块划分
3. **深入专题**: 按需阅读 `rules/` 下的专题规范

### 常用查阅场景

| 场景 | 推荐文档 |
|------|----------|
| 开发命令 (pnpm, vitest) | `CLAUDE.md` §开发命令 |
| 项目目录结构 | `rules/project-structure.md` §0 速查卡片 |
| FSD 分层和模块结构 | `rules/architecture.md` §0 速查卡片 |
| 组件设计模式 | `rules/component-design.md` §0 速查卡片 |
| 状态管理决策 | `rules/state-management.md` §0 速查卡片 |
| 代码风格和类型 | `rules/code-style.md` §0 速查卡片 |
| 测试规范 (TDD/Mock) | `rules/testing.md` §0 速查卡片 |
| 安全检查清单 | `rules/security.md` §0 速查卡片 |
| 性能优化 | `rules/performance.md` §0 速查卡片 |
| 无障碍要求 | `rules/accessibility.md` §0 速查卡片 |

---

## 文件说明

### CLAUDE.md (项目入口)

项目规范的**入口和枢纽**，包含：
- 响应语言规范（必须中文）
- 技术栈概览
- 核心开发命令
- 核心原则（组件设计、TDD）
- 规范文档导航表

### PROJECT_CONFIG.*.md (项目配置)

| 文件 | 用途 |
|------|------|
| `PROJECT_CONFIG.ai-agents-platform.md` | 本项目特定配置：功能模块、API 端点、路由配置 |
| `PROJECT_CONFIG.template.md` | 新项目配置模板，包含 `{{PLACEHOLDER}}` 占位符 |

### rules/ (专题规范)

| 文件 | 主要内容 |
|------|----------|
| `architecture.md` | Feature-Sliced Design (FSD)、分层规则、依赖方向 |
| `project-structure.md` | 项目根目录结构、配置文件速查 |
| `component-design.md` | 组件类型（展示型/容器型/复合型）、Props 设计、Hooks 规范 |
| `state-management.md` | React Query vs Zustand 决策流程、Store 设计 |
| `code-style.md` | 命名规范、类型定义、导入排序 |
| `testing.md` | TDD 循环、测试分层、Mock 规范、MSW 集成 |
| `security.md` | XSS 防护、Token 存储、环境变量安全 |
| `performance.md` | 代码分割、Memoization、性能指标 |
| `accessibility.md` | ARIA 角色、语义化 HTML、表单无障碍 |

---

## 引用关系

```
CLAUDE.md (入口)
    │
    ├─→ rules/architecture.md ──→ PROJECT_CONFIG.ai-agents-platform.md
    ├─→ rules/project-structure.md ──→ rules/architecture.md
    ├─→ rules/component-design.md
    ├─→ rules/state-management.md
    ├─→ rules/code-style.md
    ├─→ rules/testing.md ──────→ CLAUDE.md (互相引用)
    ├─→ rules/security.md
    ├─→ rules/performance.md
    ├─→ rules/accessibility.md
    ├─→ PROJECT_CONFIG.ai-agents-platform.md
    └─→ PROJECT_CONFIG.template.md
```

**引用原则**: 单向引用，CLAUDE.md 是入口，rules/ 是专题文档。

---

## 设计特点

### 速查卡片 (Section 0)

每个规范文档都有 **§0 速查卡片**，包含：
- 常用模式速查表
- PR Review 检查清单
- 常见错误提醒

> Claude 生成代码时优先查阅 §0 速查卡片

### 符号化表达

使用统一的视觉符号提高可读性：
- ✅ 正确做法
- ❌ 禁止做法
- 🔴 高优先级
- 🟡 中优先级
- 🟢 低优先级

### 模板化

`PROJECT_CONFIG.template.md` 中的占位符支持新项目快速初始化。

---

## 维护指南

### 更新文档

1. 修改规范后，确保更新对应的 §0 速查卡片
2. 新增引用时，检查是否形成循环依赖
3. 保持 CLAUDE.md 的"相关规范文档"表格同步

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 主规范 | `CLAUDE.md` | - |
| 专题规范 | `rules/{topic}.md` | `rules/testing.md` |
| 项目配置 | `PROJECT_CONFIG.{name}.md` | `PROJECT_CONFIG.ai-agents-platform.md` |
| 模板 | `PROJECT_CONFIG.template.md` | - |

### 新增文件

1. 专题规范放入 `rules/` 目录
2. 在 CLAUDE.md 的"相关规范文档"表格中添加链接
3. 添加 §0 速查卡片
4. 遵循中文优先原则

---

## 相关资源

- [Claude Code 官方文档](https://docs.anthropic.com/claude-code)
- 项目仓库: `ai-agents-platform/frontend`
