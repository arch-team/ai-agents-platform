# ADR-003: AgentCore 作为运行时基础设施

- **日期**: 2026-02-08
- **状态**: 已采纳
- **关联**: ADR-001

## 背景

平台需要 Agent 运行时环境，面临自建 vs 使用云服务的选择。竞品分析 (`docs/strategy/competitive-analysis.md`) 显示 AgentCore 是当前最完整的企业级 Agent 基础设施。

## 决策

采用 **Amazon Bedrock AgentCore** 作为 Agent 运行时基础设施，通过 Anti-Corruption Layer 模式集成。

## 理由

- **框架无关**: 支持 LangGraph, CrewAI 等主流框架，不锁定
- **模型无关**: Bedrock 内外模型均可使用
- **企业级安全**: MicroVM 隔离、IAM/OAuth 身份、VPC/PrivateLink
- **模块化服务**: Runtime, Memory, Gateway, Identity, Observability 按需组合

备选方案：
- 自建 Agent 运行时 — 开发成本高，维护负担重
- Azure AI Foundry — 与现有 AWS 技术栈不一致
- 直接使用开源框架部署 — 缺乏企业级安全和治理能力

## 影响

- `execution` 模块通过 Infrastructure 层适配器集成 AgentCore SDK
- Anti-Corruption Layer 隔离 SDK 调用，降低 API 变更影响
- 降级路径: Claude Agent SDK 直接调用 / Bedrock Converse API
- 集成架构详见 `docs/strategy/product-architecture.md` §4
