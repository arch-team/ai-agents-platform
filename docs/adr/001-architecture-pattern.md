# ADR-001: 架构模式选择

- **日期**: 2026-02-08
- **状态**: 已采纳

## 背景

项目需要支持 14 个业务模块的渐进式开发，从 MVP 到企业成熟经历 4 个阶段。需要一种既能保持模块独立性，又不过早引入微服务复杂度的架构模式。

## 决策

采用 **DDD + Modular Monolith + Clean Architecture** 三者融合。

## 理由

- **DDD 战术设计**: Entity, Value Object, Repository 等模式与 Agent 平台的业务复杂度匹配
- **Modular Monolith**: 单体部署降低运维成本，模块边界通过 EventBus 和 shared/interfaces 清晰隔离
- **Clean Architecture**: 依赖倒置确保核心业务逻辑不依赖外部框架，便于测试和替换

备选方案：
- 纯微服务 — 过早引入分布式复杂度，MVP 阶段不合适
- 简单分层架构 — 模块边界不清晰，难以支撑后期拆分

## 影响

- 后端模块四层结构: `api/ → application/ → domain/ ← infrastructure/`
- 模块间通信: EventBus (异步优先) + shared/interfaces (同步备选)
- 架构演进路径: Modular Monolith → 按需微服务拆分 (Phase 3+)
- 详细规范: `backend/.claude/rules/architecture.md`
