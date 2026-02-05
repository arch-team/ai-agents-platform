# 规范索引 (Rules Index)

> 快速查找 Claude Code 上下文规范

---

## 按概念索引

| 概念 | 文档 | 章节 |
|------|------|------|
| Construct 分层 (L1/L2/L3) | [architecture.md](rules/architecture.md) | §0.1 |
| Stack 设计 | [architecture.md](rules/architecture.md) | §2 |
| Stack 间依赖 | [architecture.md](rules/architecture.md) | §4 |
| Props 设计 | [construct-design.md](rules/construct-design.md) | §0, §1 |
| 安全默认配置 | [construct-design.md](rules/construct-design.md) | §3 |
| Grant 方法 | [security.md](rules/security.md) | §0, §1 |
| IAM 最小权限 | [security.md](rules/security.md) | §1 |
| 密钥管理 | [security.md](rules/security.md) | §2 |
| CDK Nag | [security.md](rules/security.md) | §5 |
| TDD 工作流 | [CLAUDE.md](CLAUDE.md) | 核心原则 |
| CDK Assertions | [testing.md](rules/testing.md) | §0, §2 |
| Snapshot 测试 | [testing.md](rules/testing.md) | §3 |
| 环境配置 | [deployment.md](rules/deployment.md) | §1 |
| CI/CD Pipeline | [deployment.md](rules/deployment.md) | §2 |
| 成本标签 | [cost-optimization.md](rules/cost-optimization.md) | §0, §5 |
| 环境差异化配置 | [cost-optimization.md](rules/cost-optimization.md) | §1 |
| 目录结构 | [project-structure.md](rules/project-structure.md) | §0, §1 |

---

## 按命令索引

| 命令 | 说明 | 文档 |
|------|------|------|
| `pnpm install` | 安装依赖 | [CLAUDE.md](CLAUDE.md) §开发命令 |
| `pnpm cdk synth` | 合成 CloudFormation 模板 | [CLAUDE.md](CLAUDE.md) §CDK 命令 |
| `pnpm cdk diff` | 查看变更 | [CLAUDE.md](CLAUDE.md) §CDK 命令 |
| `pnpm cdk deploy` | 部署 Stack | [deployment.md](rules/deployment.md) §0 |
| `pnpm cdk destroy` | 销毁 Stack | [CLAUDE.md](CLAUDE.md) §CDK 命令 |
| `pnpm cdk bootstrap` | 初始化 CDK | [CLAUDE.md](CLAUDE.md) §CDK 命令 |
| `pnpm test` | 运行测试 | [testing.md](rules/testing.md) §0 |
| `pnpm test:coverage` | 测试 + 覆盖率 | [CLAUDE.md](CLAUDE.md) §测试 |
| `pnpm test:watch` | 监听模式测试 | [testing.md](rules/testing.md) §0 |
| `pnpm lint` | 代码检查 | [CLAUDE.md](CLAUDE.md) §代码质量 |
| `pnpm format` | 格式化代码 | [CLAUDE.md](CLAUDE.md) §代码质量 |
| `pnpm typecheck` | 类型检查 | [CLAUDE.md](CLAUDE.md) §代码质量 |

---

## 按任务索引

| 任务 | 推荐文档 | 关键章节 |
|------|---------|---------|
| 创建新 Construct | [construct-design.md](rules/construct-design.md) | §0 模板, §2 实现 |
| 创建新 Stack | [architecture.md](rules/architecture.md) | §2 Stack 设计 |
| 添加 IAM 权限 | [security.md](rules/security.md) | §0 Grant 速查, §1 |
| 配置 Secrets | [security.md](rules/security.md) | §2 密钥管理 |
| 编写测试 | [testing.md](rules/testing.md) | §2 Fine-grained |
| 配置环境 | [deployment.md](rules/deployment.md) | §1 CDK Context |
| 部署到 AWS | [deployment.md](rules/deployment.md) | §0, §3 |
| 成本优化 | [cost-optimization.md](rules/cost-optimization.md) | §0 决策矩阵 |
| 检查项目结构 | [project-structure.md](rules/project-structure.md) | §0 速查 |
| Code Review | [architecture.md](rules/architecture.md) | §0.4 检查清单 |

---

## 速查卡片导航

每个规范文档的 **§0 速查卡片** 包含最常用的信息：

| 文档 | §0 速查卡片内容 |
|------|----------------|
| [architecture.md](rules/architecture.md) | Construct 层级表、依赖方向图、Stack 组合模式 |
| [construct-design.md](rules/construct-design.md) | Props 设计速查、Construct 模板、安全默认值 |
| [security.md](rules/security.md) | 安全规则速查表、Grant 方法速查 |
| [testing.md](rules/testing.md) | 测试命令、CDK Assertions 速查 |
| [deployment.md](rules/deployment.md) | 部署命令、环境矩阵 |
| [cost-optimization.md](rules/cost-optimization.md) | 成本优化决策矩阵、成本标签 |
| [project-structure.md](rules/project-structure.md) | Monorepo 结构、Infra 目录结构 |

---

## 文档阅读顺序建议

### 新开发者 (首次接触)
1. [CLAUDE.md](CLAUDE.md) - 技术栈、命令速查
2. [architecture.md §0](rules/architecture.md) - Construct 分层概念
3. [project-structure.md §0](rules/project-structure.md) - 目录结构

### 日常开发
- 创建资源 → [construct-design.md](rules/construct-design.md)
- 添加权限 → [security.md](rules/security.md)
- 编写测试 → [testing.md](rules/testing.md)

### 架构设计 / Code Review
- 阅读所有 `rules/` 文档
- 重点关注各文档的 §0.4 PR Review 检查清单
