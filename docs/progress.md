# 项目进度

> 每次 Claude Code 会话开始时读取此文件。会话结束时更新"当前状态"和"上次会话"。

## 当前状态

- **阶段**: Phase 1 MVP (0-3 月)
- **里程碑**: M1 项目脚手架 — 未开始
- **下一步**: 搭建后端项目脚手架 + 实现 `shared` 模块

## 模块状态

### Phase 1 (0-3 月)

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| `shared` | 待开始 | - | PydanticEntity, IRepository, EventBus, DomainError, get_db |
| `auth` | 待开始 | - | JWT, RBAC, get_current_user |
| `agents` | 待开始 | - | Agent CRUD, 状态机 (draft → active → archived) |
| `execution` | 待开始 | - | 单 Agent 对话, Bedrock AgentCore 集成, SSE |

### 后续阶段

| 阶段 | 模块 |
|------|------|
| Phase 2 | tools, knowledge, monitoring, templates |
| Phase 3 | orchestration, evaluation, models |
| Phase 4 | audit, marketplace, analytics |

## 基础设施

| CDK Stack | 状态 | 备注 |
|-----------|:----:|------|
| NetworkStack | 待开始 | VPC, Subnets, NAT Gateway |
| SecurityStack | 待开始 | Security Groups, KMS, VPC Endpoints |
| DatabaseStack | 待开始 | Aurora MySQL 3.x |

## 上次会话

> 仅保留最近一次，每次会话结束时覆盖更新此节。

- **日期**: 2026-02-08
- **完成**: 战略规划文档 (`docs/strategy/` 6 份)；项目持续性机制 (progress.md, ADR, CLAUDE.md 优化)
- **决策**: 确定 WAA 为北极星指标；架构决策记录见 `docs/adr/`
