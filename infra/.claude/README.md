# Claude Code 上下文管理

本目录包含 Claude Code 的项目上下文配置文件，用于指导 Claude 理解项目规范、架构模式和开发约定。

---

## 目录结构

```
.claude/
├── README.md                              # 本文件 - 目录说明
├── CLAUDE.md                              # 项目主规范 (入口)
├── PROJECT_CONFIG.ai-agents-platform.md   # 项目特定配置
├── PROJECT_CONFIG.template.md             # 项目配置模板
└── rules/                                 # 专题规范文档
    ├── architecture.md                    # CDK 架构规范 ★核心
    ├── project-structure.md               # 项目目录结构规范
    ├── construct-design.md                # Construct 设计规范
    ├── security.md                        # 安全规范 (IAM)
    ├── testing.md                         # 测试规范 (TDD)
    ├── deployment.md                      # 部署规范
    └── cost-optimization.md               # 成本优化规范
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
| `architecture.md` | CDK Construct 分层 (L1/L2/L3)、依赖规则、Stack 组合模式 |
| `project-structure.md` | 项目根目录结构、配置文件速查 |
| `construct-design.md` | Props 接口规范、JSDoc 注释、安全默认配置 |
| `security.md` | IAM 最小权限、Grant 方法、Secrets Manager、CDK Nag |
| `testing.md` | Fine-grained Assertions、Snapshot 测试、CDK Nag 集成 |
| `deployment.md` | 环境配置 (dev/staging/prod)、CI/CD Pipeline |
| `cost-optimization.md` | 资源选型、Reserved Instances、Cost Tags |

---

## 引用关系

| 文档 | 主要引用 | 说明 |
|------|---------|------|
| **CLAUDE.md** (入口) | 所有 rules/*.md, PROJECT_CONFIG.*.md | 项目入口，引用所有专题文档 |
| architecture.md | PROJECT_CONFIG.*.md, construct-design.md | 架构规范，引用项目配置和设计规范 |
| project-structure.md | architecture.md | 目录结构，引用架构规范 |
| construct-design.md | architecture.md, security.md, testing.md | Construct 设计，引用相关规范 |
| security.md | construct-design.md, testing.md | 安全规范，引用设计和测试 |
| testing.md | CLAUDE.md (互引), construct-design.md | 测试规范，与入口互相引用 |
| deployment.md | architecture.md, security.md, cost-optimization.md | 部署规范，引用多个相关规范 |
| cost-optimization.md | deployment.md, architecture.md | 成本优化，引用部署和架构 |

**引用原则**:
- **单向为主**: CLAUDE.md 是入口，rules/ 是专题文档
- **互引例外**: testing.md 与 CLAUDE.md 互相引用（TDD 工作流）
- **快速查找**: 使用 [RULES_INDEX.md](RULES_INDEX.md) 全局索引

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
- [AWS CDK 文档](https://docs.aws.amazon.com/cdk/)
- 项目仓库: `ai-agents-platform/infra`
