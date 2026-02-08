# 项目进度追踪

> **职责**: 项目进度的**单一真实源**，每次 Claude Code 会话开始时读取，会话结束时更新。

---

## 当前状态

| 维度 | 值 |
|------|-----|
| **当前阶段** | Phase 1 MVP (0-3 月) |
| **当前里程碑** | M1 项目脚手架 — 未开始 |
| **活跃分支** | `main` |
| **下一步** | 搭建后端项目脚手架 + 实现 `shared` 模块 |
| **阻塞项** | 无 |

---

## 模块开发状态

### Phase 1 MVP (0-3 月)

| 模块 | 状态 | 分支 | 里程碑 | 备注 |
|------|:----:|------|:------:|------|
| `shared` | 待开始 | - | M1 | PydanticEntity 基类、IRepository 接口、EventBus、DomainError 体系、get_db |
| `auth` | 待开始 | - | M1 | JWT Token 签发/验证、RBAC 角色权限、get_current_user 依赖注入 |
| `agents` | 待开始 | - | M2 | Agent CRUD、配置管理、状态机 (draft → active → archived) |
| `execution` | 待开始 | - | M3 | 单 Agent 对话执行、Bedrock AgentCore 集成、SSE 流式响应 |

**状态说明**: 待开始 | 进行中 | 已完成 | 已阻塞

### Phase 2-4 模块 (后续阶段)

| 阶段 | 模块 | 状态 |
|------|------|:----:|
| Phase 2 | `tools`, `knowledge`, `monitoring`, `templates` | 未规划 |
| Phase 3 | `orchestration`, `evaluation`, `models` | 未规划 |
| Phase 4 | `audit`, `marketplace`, `analytics` | 未规划 |

---

## 里程碑进度

### Phase 1 里程碑

| 里程碑 | 时间窗口 | 状态 | 交付物 |
|--------|---------|:----:|--------|
| **M1: 项目脚手架** | 第 1-4 周 | 待开始 | 后端 shared + auth 模块；前端脚手架 + 登录页面；CDK NetworkStack + SecurityStack + DatabaseStack |
| **M2: Agent CRUD** | 第 5-8 周 | 待开始 | agents 模块 CRUD API；前端 Agent 列表/创建/详情页面；基础 CI/CD |
| **M3: 端到端演示** | 第 9-12 周 | 待开始 | execution 模块 (单 Agent 对话)；前端 Chat 界面；端到端流程可演示 |

---

## 基础设施状态

| CDK Stack | 状态 | 环境 | 备注 |
|-----------|:----:|------|------|
| NetworkStack | 待开始 | Dev | VPC (3 AZ), Subnets, NAT Gateway |
| SecurityStack | 待开始 | Dev | Security Groups, KMS Key, VPC Endpoints |
| DatabaseStack | 待开始 | Dev | Aurora MySQL 3.x (db.t3.small 单 AZ) |

---

## 架构决策记录 (ADR)

> 重要的技术决策在此记录，为后续会话提供决策上下文。

### ADR-001: 架构模式选择

- **日期**: 2026-02-08
- **决策**: 采用 DDD + Modular Monolith + Clean Architecture
- **理由**: 模块边界清晰，支持渐进微服务拆分，DDD 战术模式与业务复杂度匹配
- **影响**: 后端模块四层结构 (api → application → domain ← infrastructure)

### ADR-002: 技术栈选型

- **日期**: 2026-02-08
- **决策**: Python 3.11+ / FastAPI / SQLAlchemy 2.0+ / MySQL (Aurora) / uv / Ruff
- **理由**: 与 Bedrock AgentCore Python SDK 生态一致，async 支持完善
- **影响**: 详见 `backend/.claude/rules/tech-stack.md`

### ADR-003: 平台基础设施选型

- **日期**: 2026-02-08
- **决策**: Amazon Bedrock AgentCore 作为 Agent 运行时基础设施
- **理由**: 框架无关 + 模型无关 + 企业级安全，详见 `docs/strategy/vision-mission.md` §7
- **影响**: execution 模块通过 Anti-Corruption Layer 适配器集成

---

## 会话日志

> 按时间倒序记录每次 Claude Code 会话的关键产出，帮助后续会话快速恢复上下文。
> 仅记录**关键决策和产出**，不记录细节过程。

### 2026-02-08: 战略规划文档

- **产出**: `docs/strategy/` 目录下 6 份文档 (2294 行, ~111KB)
  - `vision-mission.md` — 愿景、使命、差异化价值主张
  - `competitive-analysis.md` — 11 个竞品深度分析 (Tavily 研究)
  - `product-architecture.md` — 六大能力模块、三层技术映射
  - `goals-metrics.md` — WAA 北极星指标、26 项分层指标
  - `roadmap.md` — 四阶段路线图、14 个模块实现顺序
  - `README.md` — 导航文档
- **决策**: 确定北极星指标为 WAA (周活跃 Agent 数量)
- **下一步**: 搭建后端项目脚手架，开始 Phase 1 M1

---

## 会话启动模板

> 每次新 Claude Code 会话开始时，使用以下模板恢复上下文：

```
请阅读 docs/progress.md 了解项目当前进度。
今天要做的是: [具体任务描述]
```

**完整上下文恢复** (用于跨阶段或长时间中断后):

```
请阅读以下文件恢复项目上下文:
1. docs/progress.md — 当前进度
2. docs/strategy/roadmap.md — 当前阶段的详细规划
然后继续: [具体任务描述]
```
