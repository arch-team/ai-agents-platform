# AI Agents Platform 战略规划文档

> 基于 Amazon Bedrock AgentCore 的企业内部 AI Agents 平台 — 战略规划文档集

---

## 文档概览

本目录包含 AI Agents Platform 的战略规划文档，定义了项目的愿景、目标、架构蓝图和迭代路线图，作为驱动长期迭代的战略基础。

| 文档 | 内容 | 字数 |
|------|------|------|
| [vision-mission.md](vision-mission.md) | 愿景、使命、差异化价值主张 | ~4000 字 |
| [competitive-analysis.md](competitive-analysis.md) | 全面竞品分析和市场定位 | ~5000 字 |
| [product-architecture.md](product-architecture.md) | 产品能力模块、三层技术映射 | ~4000 字 |
| [goals-metrics.md](goals-metrics.md) | 北极星指标、分层指标、分阶段目标 | ~3500 字 |
| [roadmap.md](roadmap.md) | 四阶段路线图 (MVP→V1→V2→V3) | ~3500 字 |

---

## 推荐阅读顺序

```
1. vision-mission.md      为什么做？做什么？核心价值是什么？
       ↓
2. competitive-analysis.md  市场上有什么？我们的差异在哪里？
       ↓
3. product-architecture.md  产品有哪些能力模块？技术如何映射？
       ↓
4. goals-metrics.md         如何衡量成功？各阶段目标是什么？
       ↓
5. roadmap.md               具体怎么做？分几步？每步做什么？
```

**逻辑链条**: 愿景驱动 → 竞品验证定位 → 架构承载能力 → 指标衡量成功 → 路线图指导执行

---

## 核心定位

- **平台类型**: 企业内部平台 — 面向公司内部团队
- **核心技术**: Amazon Bedrock AgentCore + Claude Agent SDK
- **架构模式**: DDD + Modular Monolith + Clean Architecture (后端) | FSD (前端) | CDK (基础设施)
- **北极星指标**: 周活跃 Agent 数量 (Weekly Active Agents, WAA)

---

## 四阶段路线概览

| 阶段 | 时间 | 目标 | 核心模块 |
|------|------|------|---------|
| **Phase 1 MVP** | 0-3 月 | 端到端验证，1-2 个场景跑通 | shared → auth → agents → execution |
| **Phase 2 核心功能** | 3-6 月 | 10+ 模板，核心团队采用 | tools → knowledge → monitoring → templates |
| **Phase 3 生态扩展** | 6-12 月 | Multi-Agent 编排，全公司推广 | orchestration → evaluation → models |
| **Phase 4 企业成熟** | 12-24 月 | 平台成熟化，自助式使用 | audit → marketplace → analytics |

---

## 六大核心能力模块

| 模块 | 说明 | 后端 DDD Module | 前端 FSD Feature |
|------|------|----------------|-----------------|
| Agent 管理 | Agent 全生命周期 | `modules/agents` | `features/agents` |
| 运行时引擎 | Agent 执行与交互 | `modules/runtime` | `features/runtime` |
| 编排协作 | Multi-Agent 编排 | `modules/orchestration` | `features/orchestration` |
| 监控评估 | 可观测性与质量 | `modules/monitoring` | `features/monitoring` |
| 用户权限 | 认证授权与隔离 | `modules/auth` | `features/auth` |
| 平台基础 | 基础设施与通用 | `shared` | `shared` |

---

## 与现有规范的关系

本战略文档是对已有技术规范体系的补充，定义"做什么"和"为什么做"，而规范文档定义"怎么做"。

```
战略文档 (docs/strategy/)          规范文档 (.claude/rules/)
┌────────────────────┐           ┌────────────────────┐
│ vision-mission.md  │           │ architecture.md    │
│ competitive-analysis│ 指导方向  │ code-style.md      │
│ product-architecture│ ───────► │ testing.md         │
│ goals-metrics.md   │           │ security.md        │
│ roadmap.md         │           │ api-design.md      │
└────────────────────┘           └────────────────────┘
    战略层 (Why & What)              执行层 (How)
```

| 战略文档 | 对应规范文档 |
|---------|------------|
| product-architecture.md | backend/.claude/rules/architecture.md, frontend/.claude/rules/architecture.md, infra/.claude/rules/architecture.md |
| roadmap.md | backend/.claude/rules/tech-stack.md, infra/.claude/rules/deployment.md |
| goals-metrics.md | backend/.claude/rules/observability.md, backend/.claude/rules/testing.md |

---

## 文档维护

- **更新频率**: 建议每季度评审一次，结合阶段里程碑评审更新
- **维护责任**: 产品负责人 + 技术架构师
- **变更流程**: 重大变更需团队评审，日常更新直接提交
