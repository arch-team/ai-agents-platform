# Claude Code 上下文管理

本文档用于说明 ./infra AWS CDK 基础设施项目的Claude Code的上下文配置文件,不直接作用该项目的规范


---

## 目录结构

```
.claude/
├── README.md                              # 本文件 - Claude Code的项目上下文配置文件说明
├── CLAUDE.md                              # 项目主规范 (入口)
├── PROJECT_CONFIG.ai-agents-platform.md   # 项目特定配置
├── PROJECT_CONFIG.template.md             # 项目配置模板
└── rules/                                 # 专题规范文档
    ├── checklist.md                       # PR Review 检查清单 ★单一真实源
    ├── architecture.md                    # CDK 架构规范 ★核心
    ├── project-structure.md               # 项目目录结构规范
    ├── construct-design.md                # Construct 设计规范
    ├── security.md                        # 安全规范 (IAM)
    ├── testing.md                         # 测试规范 (TDD)
    ├── deployment.md                      # 部署规范
    ├── cost-optimization.md               # 成本优化规范
    └── tech-stack.md                      # 技术栈规范
```

---

## 快速开始

### 开发者入门

1. **阅读入口**: 从 `CLAUDE.md` 开始，了解项目概况和核心原则
2. **查阅配置**: 参考 `PROJECT_CONFIG.ai-agents-platform.md` 了解 Stack 划分
3. **深入专题**: 按需阅读 `rules/` 下的专题规范

### 常用查阅场景

| 场景 | 推荐文档 |
|------|----------|
| PR Review 检查清单 | `rules/checklist.md` |
| TDD 工作流和覆盖率 | `rules/testing.md` §0 速查卡片 |
| CDK 命令 (synth, deploy) | `CLAUDE.md` §开发命令 |
| 项目目录结构 | `rules/project-structure.md` §0 速查卡片 |
| Construct 分层和设计 | `rules/architecture.md` §0 速查卡片 |
| Construct Props 设计 | `rules/construct-design.md` §0 速查卡片 |
| IAM 权限和安全 | `rules/security.md` §0 速查卡片 |
| CDK 测试规范 | `rules/testing.md` §0 速查卡片 |
| 环境配置和部署 | `rules/deployment.md` §0 速查卡片 |
| 成本优化策略 | `rules/cost-optimization.md` §0 速查卡片 |

---

## 文件说明

### CLAUDE.md (项目入口)

项目规范的**入口和枢纽**，包含：
- 响应语言规范（必须中文）
- 技术栈概览
- 核心 CDK 命令
- 核心原则（Construct 设计、TDD）
- 规范文档导航表

### PROJECT_CONFIG.*.md (项目配置)

| 文件 | 用途 |
|------|------|
| `PROJECT_CONFIG.ai-agents-platform.md` | 本项目特定配置：Stack 列表、环境配置、AWS 账户 |
| `PROJECT_CONFIG.template.md` | 新项目配置模板，包含 `{{PLACEHOLDER}}` 占位符 |

### rules/ (专题规范)

| 文件 | 主要内容 |
|------|----------|
| `checklist.md` | PR Review 检查清单（单一真实源） |
| `architecture.md` | CDK Construct 分层 (L1/L2/L3)、依赖规则、Stack 组合模式 |
| `project-structure.md` | 项目根目录结构、配置文件速查 |
| `construct-design.md` | Props 接口规范、JSDoc 注释、安全默认配置 |
| `security.md` | IAM 最小权限、Grant 方法、Secrets Manager、CDK Nag |
| `testing.md` | TDD 工作流、覆盖率要求、Fine-grained Assertions、Snapshot 测试 |
| `deployment.md` | 环境配置 (dev/staging/prod)、CI/CD Pipeline |
| `cost-optimization.md` | 资源选型、Reserved Instances、Cost Tags |
| `tech-stack.md` | 技术栈规范 - AWS CDK 版本、依赖库版本、工具链版本要求 |

---

## 引用关系

| 文档 | 主要引用 | 说明 |
|------|---------|------|
| **CLAUDE.md** (入口) | 所有 rules/*.md, PROJECT_CONFIG.*.md | 项目入口，引用所有专题文档 |
| checklist.md | 所有 rules/*.md | PR Review 检查清单，引用各专题详细说明 |
| architecture.md | PROJECT_CONFIG.*.md, construct-design.md, deployment.md (边界) | 架构规范，与 deployment.md 有职责边界 |
| project-structure.md | architecture.md, checklist.md | 目录结构，引用架构和检查清单 |
| construct-design.md | architecture.md, security.md (边界), testing.md | 与 security.md 有职责边界 |
| security.md | construct-design.md (边界), testing.md | 与 construct-design.md 有职责边界 |
| testing.md | construct-design.md, checklist.md | 测试规范，引用设计和检查清单 |
| deployment.md | architecture.md (边界), security.md, cost-optimization.md, checklist.md | 与 architecture.md 有职责边界 |
| cost-optimization.md | deployment.md, checklist.md | 成本优化，引用部署和检查清单 |
| tech-stack.md | CLAUDE.md, construct-design.md | 技术栈规范，为其他文档提供版本基准 |

**引用原则**:
- **单向为主**: CLAUDE.md 是入口，rules/ 是专题文档
- **单一真实源**: checklist.md 是所有 PR Review 检查项的唯一来源
- **职责边界**: 相关文档通过边界说明明确各自职责
- **快速查找**: 使用 [RULES_INDEX.md](RULES_INDEX.md) 全局索引

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
- **PR Review 检查清单**: `rules/checklist.md`
- **TDD 工作流**: `rules/testing.md`
- **覆盖率要求**: `rules/testing.md`

其他文档通过链接引用，避免重复。

### 职责边界

相关文档通过边界说明明确职责分工：
- `construct-design.md` ↔ `security.md`: 代码模板 vs 安全原理
- `architecture.md` ↔ `deployment.md`: 架构设计 vs 部署执行

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
- [AWS CDK 文档](https://docs.aws.amazon.com/cdk/)
- 项目仓库: `ai-agents-platform/infra`
