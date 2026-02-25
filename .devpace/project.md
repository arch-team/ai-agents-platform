# AI Agents Platform

> 基于 Amazon Bedrock AgentCore 的企业内部 AI Agents 平台，让团队能够创建、部署和管理 AI Agent。

## 业务目标

**当前目标**：OBJ-001 — 规模化运营，支撑 50+ 活跃用户稳定使用

**成效指标（MoS）**：
- [ ] >= 50 活跃用户
- [ ] >= 40% 非技术用户自助创建 Agent
- [ ] P95 延迟 < 300ms（非 LLM 端点）
- [x] Phase 5 变更积压清零

## 实施路径

| Step | 名称 | 状态 |
|------|------|------|
| 1 | Phase 1-3: 核心平台 (M1-M7) | ✅ 完成 |
| 2 | Phase 4: 平台成熟化 (M10-M12) | ✅ 完成 |
| 3 | Phase 5A: 自动化评估 (M13) | ✅ 完成 |
| 4 | Phase 5B: 生态扩展 (M14) | ✅ 完成 |
| 5 | Phase 5C: 规模运营 (M15) | 🔄 规划完成 |

## 范围

**做什么**：
- 10 个后端业务模块 (auth/agents/execution/tool-catalog/knowledge/insights/templates/evaluation/audit/builder)
- React 19 前端 (FSD 架构, 190+ 源文件)
- AWS CDK 基础设施 (12 Stack)
- Phase 5 变更积压处理 (C-S5-1 ~ C-S5-5)

**不做什么**：
- 外部市场机制 (ADR-007 已决策移除)
- 独立 DAG 编排引擎 (ADR-008 已决策用 Agent Teams 替代)

## 项目原则

- SDK-First: 封装 < 100 行，优先使用成熟 SDK (ADR-006)
- DDD + Modular Monolith: 模块隔离 R1/R3，shared/interfaces 跨模块通信
- TDD: 先写测试再实现，覆盖率 >= 85%
- 中文优先: 所有对话、文档、代码注释使用中文

## 价值功能树

```
OBJ-001（规模化运营）
├── BR-001：技术债务清理 ✅
│   ├── PF-001：依赖引入完善 → CR-001 ✅ merged
│   ├── PF-002：类型系统治理 → CR-002 ✅ merged
│   └── PF-003：LDAP 集成补全 → CR-003 ✅ merged
├── BR-002：运维监控强化 ✅
│   ├── PF-004：SSE 并发监控 → CR-004 ✅ merged
│   └── PF-005：LDAP 网络配置 → CR-005 ✅ merged
├── BR-003：多租户成本管理 (M15)
│   ├── PF-006：billing 模块 — 部门预算配额 → CR-008 ✅ merged
│   ├── PF-007：billing 模块 — ROI 自动报告 → (待创建 CR)
│   └── PF-008：department_id 渐进迁移 → CR-006 ✅ merged
├── BR-004：运营基础设施 (M15)
│   └── PF-009：BillingStack CDK → CR-007 ✅ merged
├── BR-005：性能保障 (M15)
│   └── PF-010：P95 性能验证 + 优化 → (待创建 CR)
└── BR-006：前端补全 (M15)
    └── PF-011：前端 BillingPage → (待创建 CR)
```
