# 架构决策记录 (ADR)

> 记录项目中重要的技术决策，为后续开发提供决策上下文。

## ADR 索引

| 编号 | 标题 | 日期 | 状态 |
|------|------|------|:----:|
| [001](001-architecture-pattern.md) | 架构模式: DDD + Modular Monolith | 2026-02-08 | 已采纳 |
| [002](002-tech-stack.md) | 技术栈选型 | 2026-02-08 | 已采纳 |
| [003](003-agentcore-infrastructure.md) | AgentCore 作为运行时基础设施 | 2026-02-08 | 已采纳 |
| [005](005-database-engine-selection.md) | 数据库引擎选型: MySQL + Bedrock Knowledge Bases | 2026-02-10 | 已采纳 |
| [006](006-agent-framework-selection.md) | Agent 框架选型: Claude Agent SDK + Claude Code CLI | 2026-02-10 | 已采纳 |
| [007](007-phase3-adjustment.md) | Phase 3 路线图调整 | 2026-02-12 | 已采纳 |
| [008](008-agent-teams-over-dag-engine.md) | Agent Teams 替代 DAG 引擎 | 2026-02-12 | 已采纳 |
| [009](009-phase3-quarterly-review.md) | Phase 3 季度回顾 | 2026-02-12 | 已采纳 |
| [010](010-opus-46-model-evaluation.md) | Opus 4.6 模型集成评估: 模型选择策略与成本分析 | 2026-02-13 | 已采纳 |
| [012](012-blue-green-deployment.md) | 蓝绿部署引入时机评估: 50 并发规模下滚动更新增强 | 2026-02-14 | 已采纳 |
| [013](013-strands-evaluation.md) | Strands Agents SDK 战略评估: 不迁移，保持观察 | 2026-02-14 | 已采纳 |

## ADR 模板

新建 ADR 时复制以下模板：

```markdown
# ADR-NNN: 标题

- **日期**: YYYY-MM-DD
- **状态**: 提议 | 已采纳 | 已废弃 | 已替代
- **关联**: ADR-XXX (如有)

## 背景

什么情况下需要做这个决策？

## 决策

选择了什么方案？

## 理由

为什么选择这个方案？考虑了哪些备选方案？

## 影响

这个决策对项目的影响是什么？
```
