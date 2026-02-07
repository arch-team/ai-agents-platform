# Claude Code 上下文管理

> **职责**: `.claude/` 目录的导航说明，帮助开发者快速定位规范文档。本文档位于 `doc/` 目录，用于说明 ./backend Python 后端项目的 Claude Code 的上下文配置文件，不直接作用该项目的规范

---

## 目录结构

```
.claude/
├── CLAUDE.md                           # 项目主规范 (入口)
├── project-config.md                   # 项目特定配置
├── settings.local.json                 # Claude Code 本地权限配置
└── rules/                              # 专题规范文档
    ├── tech-stack.md                   # 技术栈版本规范 (单一真实源) ★
    ├── checklist.md                    # PR Review 检查清单 ★单一真实源
    ├── architecture.md                 # 架构规范 ★核心
    ├── project-structure.md            # 项目目录结构规范
    ├── code-style.md                   # 代码风格规范
    ├── testing.md                      # 测试规范 (TDD)
    ├── security.md                     # 安全规范
    ├── sdk-first.md                    # SDK 优先原则
    └── api-design.md                   # API 设计规范
```

---

## 快速开始

### 开发者入门

1. **阅读入口**: 从 `CLAUDE.md` 开始，了解项目概况和核心原则
2. **查阅配置**: 参考 `project-config.md` 了解模块划分
3. **深入专题**: 按需阅读 `rules/` 下的专题规范

### 常用查阅场景

| 场景 | 推荐文档 |
|------|----------|
| 开发命令 (uv, pytest, ruff) | `CLAUDE.md` §开发命令 |
| 技术栈版本确认 | `rules/tech-stack.md` |
| PR Review 检查清单 | `rules/checklist.md` |
| 项目目录结构 | `rules/project-structure.md` §0 速查卡片 |
| 模块结构和分层 | `rules/architecture.md` §0 速查卡片 |
| 代码风格和类型提示 | `rules/code-style.md` §0 速查卡片 |
| 测试规范 (TDD/Mock) | `rules/testing.md` §0 速查卡片 |
| 安全检查清单 | `rules/security.md` §0 速查卡片 |
| API 路由和状态码 | `rules/api-design.md` |
| SDK 使用决策 | `rules/sdk-first.md` |

---

## 文件说明

### CLAUDE.md (项目入口)

项目规范的**入口和枢纽**，包含：
- 响应语言规范（必须中文）
- 技术栈概览
- 核心开发命令
- 核心原则（SDK-First、TDD）
- 规范文档导航表

### project-config*.md (项目配置)

| 文件 | 用途 |
|------|------|
| `project-config.md` | 本项目特定配置：模块列表、域事件、跨模块接口 |
| `project-config.template.md` | 新项目配置模板，包含 `{{PLACEHOLDER}}` 占位符（位于 `doc/` 目录） |

### rules/ (专题规范)

| 文件 | 主要内容 |
|------|----------|
| `tech-stack.md` | **技术栈版本的单一真实源** - Python、FastAPI、SQLAlchemy 等核心依赖版本 |
| `checklist.md` | **PR Review 检查清单（单一真实源）** - 架构、代码风格、安全、测试、API 设计检查项 |
| `architecture.md` | 架构模式 (DDD + Modular Monolith + Clean Architecture)、分层规则、模块隔离黄金法则、DDD 战术模式 |
| `project-structure.md` | 项目根目录结构、配置文件速查、初始化检查清单 |
| `code-style.md` | 类型提示、命名规范、Docstring 原则、异步代码规范 |
| `testing.md` | TDD 循环、测试分层、AAA 模式、Mock 规范、覆盖率配置 |
| `security.md` | 禁止事项（注入、硬编码）、必须事项（验证、哈希）、安全检查命令 |
| `sdk-first.md` | SDK 决策流程、优先级说明、异常处理模式 |
| `api-design.md` | RESTful 路由、HTTP 状态码、分页规范、错误响应格式 |

### settings.local.json

Claude Code 的本地权限配置，包含：
- 允许的 Bash 命令
- WebFetch 允许的域名
- MCP 服务器权限

---

## 引用关系

```
CLAUDE.md (入口)
    │
    ├─→ rules/tech-stack.md (技术栈版本)
    ├─→ rules/checklist.md (PR Review 检查清单)
    ├─→ rules/architecture.md ──→ project-config.md
    ├─→ rules/project-structure.md ──→ rules/architecture.md, rules/testing.md
    ├─→ rules/code-style.md
    ├─→ rules/testing.md ──────→ CLAUDE.md (互相引用)
    ├─→ rules/security.md
    ├─→ rules/sdk-first.md
    ├─→ rules/api-design.md
    └─→ project-config.md
```

**引用原则**:
- **单向为主**: CLAUDE.md 是入口，rules/ 是专题文档
- **单一真实源**: checklist.md 是所有 PR Review 检查项的唯一来源

---

## 设计特点

### 速查卡片 (Section 0)

每个规范文档都有 **§0 速查卡片**，包含：
- 常用模式速查表
- 常见错误提醒

> Claude 生成代码时优先查阅 §0 速查卡片
>
> PR Review 检查清单见 `rules/checklist.md`（单一真实源）

### 单一真实源 (SSOT)

关键信息只在一个地方定义：
- **技术栈版本**: `rules/tech-stack.md`
- **PR Review 检查清单**: `rules/checklist.md`
- **架构规范**: `rules/architecture.md`

其他文档通过链接引用，避免重复。

### 符号化表达

使用统一的视觉符号提高可读性：
- ✅ 正确做法
- ❌ 禁止做法
- 🔴 高优先级
- 🟡 中优先级
- 🟢 低优先级

### 模板化

`project-config.template.md`（位于 `doc/` 目录）和 `rules/architecture.md` 中的占位符支持新项目快速初始化。

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
| 项目配置 | `project-config.md` | - |

### 新增文件

1. 专题规范放入 `rules/` 目录
2. 在 CLAUDE.md 的"相关规范文档"表格中添加链接
3. 添加 §0 速查卡片
4. 遵循中文优先原则

### 演进策略

- **开发过程中**: 使用 Claude Code 的 `#` 快捷键，将开发中发现的模式和 gotchas 自动写入 CLAUDE.md
- **定期审计**: 使用 `/claude-md-improver` 检查规范与实际代码的匹配度和时效性
- **新模块添加**: 同步更新 `project-config.md` 的模块列表和域事件表
- **技术栈升级**: 更新 `rules/tech-stack.md`（单一真实源），其他文档通过引用自动保持一致

---

## 相关资源

- [Claude Code 官方文档](https://docs.anthropic.com/claude-code)
- 项目仓库: `ai-agents-platform`
