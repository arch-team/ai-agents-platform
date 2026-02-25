# 迭代: M15 规模运营

- **目标**: 构建 billing 模块 + 部门隔离，支撑 50+ 活跃用户的成本归因和预算管理
- **周期**: 2026-02-24 ~ 2026-04-07 (约 6 周)
- **MoS**: 每部门独立成本视图 | P95 < 300ms (非 LLM) | billing 前端可用

## 产品功能

| PF | 名称 | 复杂度 | CR | 状态 |
|----|------|:------:|---:|:----:|
| PF-006 | billing 模块 — 部门预算配额 | L | CR-008 | ✅ |
| PF-007 | billing 模块 — ROI 自动报告 | M | CR-009 | ✅ |
| PF-008 | department_id 渐进迁移 | L | CR-006 | ✅ |
| PF-009 | BillingStack CDK | M | CR-007 | ✅ |
| PF-010 | P95 性能验证 + 优化 | S | — | ⏳ |
| PF-011 | 前端 BillingPage | M | — | ⏳ |

## 依赖与风险

- R4 (高): department_id 迁移需 Alembic 预演，允许 NULL 渐进填充
- 依赖 AWS Cost Explorer API 和 Organizations API 权限配置
- PF-008 (department_id) 应优先完成，其余 PF 依赖此基础

## 建议执行顺序

```
Week 1-2: PF-008 (department_id 迁移) + PF-009 (BillingStack CDK) — 基础设施先行
Week 3-4: PF-006 (billing 部门预算) + PF-007 (ROI 报告) — 核心业务逻辑
Week 5:   PF-011 (BillingPage 前端) — 依赖后端 API
Week 6:   PF-010 (P95 性能验证) + 质量验收
```
