# 四阶段迭代路线图

> **文档类型**: 战略规划 | **维护者**: 后端架构师 | **状态**: v1.2 — Phase 2 完成后评审调整 (C-S3-3)

---

## 1. 路线图概述

### 1.1 四阶段总览

```
Phase 1: MVP 基础        Phase 2: 核心功能        Phase 3: 生态扩展        Phase 4: 企业成熟
   (0-3 月) ✅              (3-6 月) ✅              (6-12 月)               (12-18 月)
┌──────────────┐     ┌──────────────┐      ┌──────────────┐       ┌──────────────┐
│ 端到端验证    │ ──► │ 完善核心能力  │ ──► │ Multi-Agent   │ ──►  │ 平台成熟化    │
│ 1-2 业务场景  │     │ 10+ 模板     │      │ 全公司推广    │       │ 自助式使用    │
│ 跑通         │     │ 核心团队使用  │      │              │       │              │
└──────────────┘     └──────────────┘      └──────────────┘       └──────────────┘

后端模块:              后端模块:               后端模块:               后端模块:
  shared → auth         tool-catalog           orchestration           audit
  agents → execution    knowledge              evaluation              marketplace
                        insights                                       analytics
                        templates

CDK Stacks:            CDK Stacks:             CDK Stacks:             CDK Stacks:
  Network + Security    Compute + Api           Monitoring 增强         多区域部署
  Database              AgentCore (Runtime      Prod 环境              灾备方案
  基础 CI/CD              + Gateway)            蓝绿部署
                        Staging 环境
```

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **增量交付** | 每个阶段交付可独立运行的业务价值，不依赖后续阶段完成 |
| **技术债务控制** | 每阶段预留 15-20% 工时用于偿还技术债务和架构改进 |
| **业务价值驱动** | 模块实现顺序由业务场景依赖关系决定，非技术偏好 |
| **架构一致性** | 所有阶段遵循已定义的 DDD + Modular Monolith + Clean Architecture |
| **可观测先行** | 从 Phase 1 开始内建日志、指标和健康检查 |

---

## 2. Phase 1: MVP 基础 (0-3 月)

### 2.1 目标

端到端验证核心流程，1-2 个业务场景跑通。用户可以登录平台、创建 Agent、与 Agent 进行对话交互。

### 2.2 后端模块实现顺序

模块按技术依赖关系排列，后续模块依赖前序模块提供的基础能力。

| 顺序 | 模块 | 职责 | 依赖 |
|:----:|------|------|------|
| 1 | `shared` | 共享内核 - `PydanticEntity` 基类、`IRepository` 泛型接口、`EventBus`、`DomainError` 异常体系、`get_db` 数据库会话 | 无 |
| 2 | `auth` | 用户认证授权 - JWT Token 签发/验证、RBAC 角色权限、`get_current_user` 依赖注入 | shared |
| 3 | `agents` | Agent 管理 - Agent CRUD、配置管理、状态机 (draft → active → archived) | shared, auth |
| 4 | `execution` | 任务执行引擎 - 单 Agent 对话执行、SSE 流式响应。**ADR-006**: IAgentRuntime 接口 + Claude Agent SDK (ClaudeAgentAdapter)，通过 AgentCore Runtime 部署 | shared, auth, agents |

每个模块严格遵循四层结构: `api/ → application/ → domain/ ← infrastructure/`，模块间通过 EventBus 异步解耦或 `shared/domain/interfaces/` 同步调用。

### 2.3 前端功能

基于 FSD 分层 (app → pages → widgets → features → entities → shared):

| 层级 | 实现内容 |
|------|---------|
| **shared** | API Client (axios 封装)、UI 基础组件 (Button, Input, Card)、路由守卫 |
| **entities** | User 实体模型 + 类型定义、Agent 实体模型 + AgentCard 基础 UI |
| **features** | auth/LoginForm (React Hook Form + Zod)、agents/AgentList、agents/AgentCreate、execution/ChatInterface |
| **widgets** | Header (导航 + 用户菜单)、Sidebar (侧边栏导航) |
| **pages** | LoginPage、DashboardPage、AgentListPage、AgentDetailPage、ChatPage |
| **app** | App.tsx、路由配置 (React Router + lazy 加载)、QueryProvider、AuthProvider |

### 2.4 基础设施

| CDK Stack | 包含资源 | 说明 |
|-----------|---------|------|
| **NetworkStack** | VPC (3 AZ)、Subnets (Public/Private/Isolated)、NAT Gateway (Dev 环境 1 个) | 网络基础，所有 Stack 的依赖 |
| **SecurityStack** | Security Groups、KMS Key、VPC Endpoints (S3 Gateway) | 安全基础配置 |
| **DatabaseStack** | Aurora MySQL 3.x (Dev: db.t3.small 单 AZ)、Secrets Manager (DB 密码) | 数据存储层 |

CI/CD: GitHub Actions 基础 Pipeline (lint → test → cdk synth → deploy dev)

### 2.5 关键里程碑

| 里程碑 | 时间窗口 | 交付物 |
|--------|---------|--------|
| **M1: 项目脚手架** | 第 1-4 周 | 后端 shared + auth 模块完成；前端脚手架 + 登录页面；NetworkStack + SecurityStack + DatabaseStack 部署 Dev 环境 |
| **M2: Agent CRUD** | 第 5-8 周 | agents 模块 CRUD API 完成；前端 Agent 列表/创建/详情页面；基础 CI/CD Pipeline |
| **M3: 端到端演示** | 第 9-12 周 | execution 模块完成 (单 Agent 对话)；前端 Chat 界面；端到端流程可演示 |

### 2.6 验收标准

| 指标 | 目标值 |
|------|--------|
| 功能完整性 | 用户可登录、创建 Agent、执行对话 |
| API 可用性 | >= 95% (Dev 环境) |
| 单元测试覆盖率 | >= 85% (后端)、>= 80% (前端) |
| 响应延迟 | P95 < 500ms (非 LLM 接口)、P95 < 10s (LLM 对话接口) |
| 安全基线 | JWT 认证、RBAC 授权、密码 bcrypt 哈希、无硬编码密钥 |

---

## 3. Phase 2: 核心功能 (3-6 月)

### 3.1 目标

完善核心能力，提供 10+ Agent 模板，核心团队开始日常使用平台。

### 3.2 后端模块实现顺序

| 顺序 | 模块 | 职责 | 依赖 |
|:----:|------|------|------|
| 5 | `tool-catalog` | 企业工具目录 - 工具注册/发现/审批、MCP Server 目录管理、权限管控与调用审计 | shared, auth, agents |
| 6 | `knowledge` | 知识库管理 - 文档上传/解析、向量化存储、RAG 检索集成 | shared, auth, agents |
| 7 | `insights` | 业务洞察与成本归因 - 消费 AgentCore Observability 数据、Token 成本按团队/项目归因、使用趋势分析 | shared, auth, execution |
| 8 | `templates` | Agent 模板管理 - 模板 CRUD、模板实例化、分类标签 | shared, auth, agents, tool-catalog, knowledge |

`templates` 模块排在最后，因为它需要聚合 agents、tool-catalog、knowledge 的配置来定义完整的 Agent 模板。

### 3.3 前端功能

| 功能模块 | 关键页面/组件 |
|---------|-------------|
| 工具目录 | ToolCatalogPage (工具浏览/搜索/审批)、McpServerRegistryForm (MCP Server 注册)、ToolCard (entities 层) |
| 知识库管理 | KnowledgeBasePage (文档列表)、FileUploadWidget (拖拽上传)、DocumentPreview |
| 业务洞察仪表板 | InsightsDashboardPage (成本归因/使用趋势)、TokenCostChart、UsageTrendTable |
| 模板市场 | TemplateMarketPage (模板浏览)、TemplateDetailPage、CreateFromTemplateForm |

### 3.4 基础设施

| CDK Stack | 新增资源 | 说明 |
|-----------|---------|------|
| **ComputeStack** | ECS Fargate Service (Platform API)、ALB、Auto Scaling | 平台 API 容器化部署 |
| **AgentCoreStack** | AgentCore Runtime (Agent 执行层)、AgentCore Gateway (MCP 统一入口) | Agent 运行时部署 (ADR-006) |
| **ApiStack** | API Gateway、WAF 规则、访问日志 | API 入口层 |

新增 Staging 环境，资源配置参考环境矩阵 (db.t3.medium 多 AZ)。集成 CloudWatch 监控 (日志组、基础告警)。AgentCore CDK 使用 `@aws-cdk/aws-bedrock-agentcore-alpha` L2 Construct。

### 3.5 关键里程碑

| 里程碑 | 时间窗口 | 交付物 |
|--------|---------|--------|
| **M4: 工具目录** | 第 13-16 周 | tool-catalog 模块完成；MCP Server 注册与审批流程；前端工具目录界面 |
| **M5: 知识库 + 业务洞察** | 第 17-20 周 | knowledge 模块 (RAG 集成)；insights 模块 (成本归因/使用趋势)；前端仪表板 |
| **M5.5: AgentCore 基础集成** | M5 完成后 | AgentCore 集成 P0 (依赖升级 + IAgentRuntime/IToolQuerier 接口 + runtime_type + 可观测性基础) + P1 (StrandsAgentAdapter + AgentCore Runtime CDK) — 详见 `agentcore-integration-plan.md` |
| **M6: 模板生态** | 第 21-24 周 | templates 模块 + 10 个预置模板；ComputeStack + AgentCoreStack + ApiStack 部署 Staging |

### 3.6 验收标准

| 指标 | 目标值 |
|------|--------|
| Agent 模板数量 | >= 10 个覆盖常见业务场景 |
| 核心团队活跃用户 | >= 5 人日常使用 |
| API 可用性 | >= 99% (Staging 环境) |
| 单元测试覆盖率 | >= 85% (后端)、>= 80% (前端) |
| 知识库检索准确率 | Top-5 召回率 >= 80% |
| 成本归因覆盖率 | 所有 Agent 执行均有按团队/项目维度的成本归因 |

### 3.7 Phase 2 经验教训（2026-02-11 评审补充）

> 本节记录 Phase 2 开发过程中的关键经验和踩坑，为 Phase 3 规划提供输入。

#### 数据库兼容性

| 问题 | 影响 | 解决方案 | Phase 3 启示 |
|------|------|---------|-------------|
| MySQL TEXT 列不支持 `server_default` | Alembic 迁移失败 | 移除 TEXT 列默认值，仅在 Python 层设置 | 新模块建表前查阅 MySQL 方言限制 |
| SQLAlchemy `autocommit` 行为差异 | 端到端测试写入丢失 | 强制 `session.commit()` + `get_db` auto-commit/rollback | Repository 层统一显式 commit 模式 |
| SQLite vs MySQL 测试差异 (5+ 方言) | 测试通过但部署失败 | 新增 MySQL 集成测试 (`docker-compose`) | Phase 3 所有 Repository 测试同时运行 SQLite + MySQL |

#### 容器化与部署

| 问题 | 影响 | 解决方案 | Phase 3 启示 |
|------|------|---------|-------------|
| ARM64 vs AMD64 架构 | ECS Fargate 容器启动失败 | 强制 `--platform linux/amd64` 构建 | Dockerfile 必须指定 `LINUX_AMD64` 平台 |
| Docker Hub 拉取限流 | CI/CD 构建失败 | 替换为 ECR Public 镜像源 | 所有基础镜像统一使用 ECR Public |
| ECS 健康检查 `curl` 不可用 | 健康检查失败导致服务滚动部署失败 | 用 `python -c "import httpx; ..."` 替代 curl | Agent Runtime 容器也需注意内置工具可用性 |
| Aurora 版本/实例类型兼容 | `db.t3.small` 不支持 Aurora 3.10.0 | 升级到 `db.t3.medium` | 新实例类型选型前查阅 Aurora 版本兼容矩阵 |

#### CDK 与 AgentCore

| 问题 | 影响 | 解决方案 | Phase 3 启示 |
|------|------|---------|-------------|
| AgentCore AZ 限制 | Runtime 不支持所有 AZ | CDK 限定可用 AZ (us-east-1a/1b) | 部署前检查 AgentCore 区域可用性 |
| SG description 仅限 ASCII | CDK deploy 失败 (中文描述) | Security Group 描述统一使用英文 | CDK 代码中避免中文参数 |
| `@aws-cdk/aws-bedrock-agentcore-alpha` 为 alpha | API 可能变更 | 锁定版本 + 封装层隔离 | P2/P3 集成时预留 L1 CfnResource 降级路径 |

#### 工程实践

| 经验 | 说明 | Phase 3 建议 |
|------|------|-------------|
| 五维度审查价值高 | Phase 2 审查发现 64 项问题，S0-S2 全部修复后系统质量显著提升 | Phase 3 启动前再做一轮审查 |
| 变更积压管理有效 | S0-S4 分级穿插执行，避免技术债务累积 | 保留变更积压机制 |
| TDD + 1427 测试 | 测试覆盖率 > 94%，重构时信心高 | orchestration 模块复杂度高，TDD 更关键 |
| 并行 Agent 开发模式 | 多 Agent 并行处理 3 子项目 7 维度效率高 | Phase 3 可继续使用并行模式 |

---

## 4. Phase 3: 生态扩展 (6-12 月) — 已调整

### 4.1 目标

实现 Multi-Agent 编排能力，完成 AgentCore 平台能力集成 (P2/P3)，平台向核心团队全面推广。

> **调整说明** (C-S3-3): 原规划假设 Phase 2 结束时 AgentCore 集成已完成，但实际 P0+P1 完成后 P2/P3 仍有 6 项未完成。Phase 3 需同时完成 AgentCore 深度集成 + orchestration 模块。生产部署目标从"全公司推广"调整为"核心团队全面使用 + Staging 验证"，Prod 环境部署前移至 Phase 3 末尾而非单独里程碑。

### 4.2 Phase 3 就绪度评估

Phase 3 的核心依赖项当前状态：

| 依赖项 | 状态 | 风险评估 |
|--------|:----:|---------|
| AgentCore Runtime | ✅ 已部署 (2 AZ) | 低 — 已验证 |
| AgentCore Gateway | ✅ 已部署 (MCP) | 低 — 已验证 |
| ECR 镜像仓库 | ✅ 已就绪 | 低 |
| Claude Agent SDK + IAgentRuntime | ✅ P0+P1 完成 | 低 — ClaudeAgentAdapter 已实现 |
| IToolQuerier 跨模块接口 | ✅ P0 完成 | 低 |
| AgentCore Gateway 集成 (P2-1) | ❌ 未开始 | 中 — orchestration 需要工具路由 |
| AgentCore Memory (P2-2) | ❌ 未开始 | 中 — 多 Agent 编排需要会话记忆 |
| OpenTelemetry (P2-3) | ❌ 未开始 | 低 — 独立于业务逻辑 |
| CI/CD Pipeline (C-S4-1) | ❌ 未开始 | 中 — 影响部署效率 |
| Secrets 管理统一 (C-S4-3) | ❌ 未开始 | 中 — Prod 部署前必须完成 |
| 基础监控告警 (C-S4-4) | ❌ 未开始 | 高 — Prod 环境运维前提 |

**结论**: orchestration 模块的核心技术依赖 (Runtime + Gateway + SDK) 已就绪。主要风险在于 P2 平台能力和 S4 运维基础设施未完成，需在 Phase 3 前期集中处理。

### 4.3 后端模块实现顺序

| 顺序 | 模块 | 职责 | 依赖 | 调整说明 |
|:----:|------|------|------|---------|
| 9 | `orchestration` | Multi-Agent 工作流编排 - DAG 定义/执行引擎、Agent 间消息路由、并行/串行执行策略。基于 Claude Agent SDK 子 Agent (Task 工具) + AgentCore Runtime A2A 协议 | shared, auth, agents, execution, tool-catalog | 不变 |
| 10 | `evaluation` | Agent 质量评估 - 评估数据集管理、自定义业务评估指标、评估报告。**简化**: 初期不依赖 AgentCore Evaluations，自建轻量评估框架 | shared, auth, agents, execution | 简化范围，移除对 AgentCore Evaluations 的硬依赖 |

**调整理由**: AgentCore Evaluations 目前为预览版，API 稳定性不确定。evaluation 模块初期以自建评估框架为主（测试集定义 + 批量执行 + 评分），后续 AgentCore Evaluations GA 后可平滑切换。

### 4.4 前端功能

| 功能模块 | 关键页面/组件 |
|---------|-------------|
| 可视化编排器 | OrchestrationEditorPage (拖拽式 DAG 编辑器)、NodePalette (Agent/Tool 节点面板)、FlowCanvas (画布)、ConnectionLine |
| 评估报告 | EvaluationDashboardPage (评估结果总览)、TestCaseRunner (测试执行)、ScoreRadarChart |

### 4.5 基础设施

| CDK Stack | 变更 | 说明 | 调整说明 |
|-----------|------|------|---------|
| **MonitoringStack** | 新增: OpenTelemetry (ADOT) + CloudWatch Dashboards + SNS 告警 | 全链路可观测 (P2-3 + C-S4-4) | **前移**: 从 Phase 3 中期前移到 M7 之前，作为 AgentCore P2 集成的一部分 |
| **ComputeStack** | 增强: 蓝绿部署 (CodeDeploy)、Auto Scaling 策略优化 | 零停机部署 | 不变 |
| **Staging 环境** | 增强: 完整 Prod 配置验证 | Prod 部署前验证 | 新增 — Staging 作为 Prod 镜像环境 |
| **Prod 环境** | 全量 Stack 部署: db.r6g.large 多 AZ、每 AZ 一个 NAT Gateway | 生产就绪 | 不变 |

### 4.6 关键里程碑 — 已调整

| 里程碑 | 时间窗口 | 交付物 | 调整说明 |
|--------|---------|--------|---------|
| **M7-prep: AgentCore P2 + 运维基础** | 第 25-28 周 | AgentCore Gateway 工具同步 (P2-1) + Memory MCP 桥接 (P2-2) + OpenTelemetry (P2-3) + CI/CD (C-S4-1) + Secrets 统一 (C-S4-3) + 监控告警 (C-S4-4) | **新增**: 将 P2 集成和剩余 S4 变更集中处理，为 orchestration 扫清依赖 |
| **M7: Multi-Agent 编排** | 第 29-36 周 | orchestration 模块完成；支持串行/并行/条件分支；Claude Agent SDK 子 Agent + AgentCore Memory 集成 | 原 8 周时间窗口不变，但起始时间后移 4 周（等待 M7-prep 完成） |
| **M8: 评估体系** | 第 37-42 周 | evaluation 模块（自建轻量评估框架）+ 自动化评估 Pipeline | 简化范围: 不依赖 AgentCore Evaluations 预览版 |
| **M9: 生产部署** | 第 43-48 周 | Staging 全面验证 → Prod 环境部署 + 蓝绿部署验证 + 核心团队全面推广 (目标 20+ 活跃用户) | 用户目标从 50 调整为 20，更符合内部平台初期推广实际 |

### 4.7 验收标准 — 已调整

| 指标 | 目标值 | 调整说明 |
|------|--------|---------|
| 编排工作流支持 | 串行、并行、条件分支三种模式 | 不变 |
| 核心团队活跃用户 | >= 20 人 | 原 50 人 → 20 人，内部平台初期推广更务实 |
| API 可用性 | >= 99.5% (Prod 环境) | 不变 |
| 部署成功率 | >= 99% (蓝绿部署) | 不变 |
| Agent 评估覆盖率 | 所有公开模板均有基线评估分数 | 不变 |
| P95 响应延迟 | < 300ms (非 LLM 接口) | 不变 |
| AgentCore 集成覆盖 | Gateway + Memory + Observability 全部完成 (P2 3/3) | 新增 |
| 运维成熟度 | CI/CD + Secrets + 监控告警全部就位 | 新增 |

---

## 5. Phase 4: 企业成熟 (12-18 月) — 已调整

> **调整说明** (C-S3-3): 时间窗口从 12-24 月缩短至 12-18 月。移除 marketplace 和多区域部署（200 人以内的内部平台不需要市场机制和跨区域容灾），降低灾备指标至合理水平。保留 audit 模块作为核心交付，analytics 简化为 insights 模块的增强而非独立模块。

### 5.1 目标

平台成熟化，完善合规审计和使用分析，支撑全公司推广使用。

### 5.2 后端模块实现顺序

| 顺序 | 模块 | 职责 | 依赖 | 调整说明 |
|:----:|------|------|------|---------|
| 11 | `audit` | 审计日志与合规 - 全操作审计追踪、合规报告生成、数据保留策略 | shared, auth (全模块事件订阅) | 不变 |
| ~~12~~ | ~~`marketplace`~~ | ~~Agent 市场/分享~~ | - | **移除**: 200 人内部平台无需市场机制；模板分享通过 templates 模块已满足 |
| ~~13~~ | ~~`analytics`~~ | ~~使用分析与洞察~~ | - | **降级**: 合并为 insights 模块增强（新增用户行为分析和 ROI 计算），不再独立建模块 |

`audit` 是本阶段唯一新建模块。Phase 2 的 `insights` 模块在本阶段增强（用户行为分析、ROI 计算），不单独建 `analytics` 模块。

### 5.3 前端功能

| 功能模块 | 关键页面/组件 | 调整说明 |
|---------|-------------|---------|
| 审计与合规 | AuditLogPage (审计日志查询)、ComplianceReportPage (合规报告)、DataRetentionSettings | 不变 |
| 增强分析看板 | InsightsDashboardPage 增强 (用户行为分析、ROI 计算、使用趋势) | 原 analytics 降级为 insights 增强 |
| 自助式 Agent 构建器 | AgentBuilderPage (低代码拖拽构建)、PromptEditor (提示词编辑器)、PreviewPanel (实时预览) | 保留，核心降低门槛功能 |

### 5.4 基础设施

| 能力 | 实现方案 | 说明 | 调整说明 |
|------|---------|------|---------|
| ~~**多区域部署**~~ | ~~CDK Pipeline + 多区域 Stack 实例化~~ | - | **移除**: 内部平台用户量不支撑多区域 ROI |
| **灾备方案** | Aurora 跨 AZ 高可用 + S3 版本管理 + 定期快照 | RPO < 5min, RTO < 15min | **降级**: 原金融级目标 (RPO<1s) → 内部平台合理目标 |
| **成本优化** | AWS Budgets 告警 + Dev 环境定时缩减 + Savings Plans 评估 | 目标: Dev 环境成本降低 50% | 简化 — 聚焦 Dev 环境成本优化 |

### 5.5 关键里程碑

| 里程碑 | 时间窗口 | 交付物 |
|--------|---------|--------|
| **M10: 审计合规** | 第 49-56 周 | audit 模块完成；全操作审计追踪；合规报告自动生成 |
| **M11: 平台成熟化** | 第 57-64 周 | insights 增强 (ROI + 用户行为)；自助式 Agent 构建器；灾备方案验证 |
| **M12: 全公司推广** | 第 65-72 周 | 全公司推广 (目标 50+ 活跃用户)；成本优化；AgentCore P3 深度集成 (Identity + 长期记忆策略) |

### 5.6 验收标准 — 已调整

| 指标 | 目标值 | 调整说明 |
|------|--------|---------|
| 全公司活跃用户 | >= 50 人 | 原 200 人 → 50 人，阶段性目标更务实 |
| ~~Agent 市场发布数~~ | ~~>= 50 个~~ | 移除 — marketplace 已移除 |
| 自助创建比例 | >= 40% 的 Agent 由非技术人员自助创建 | 原 60% → 40%，内部平台技术用户比例高 |
| API 可用性 | >= 99.9% (Prod 环境) | 不变 |
| 审计覆盖率 | 100% 写操作有审计日志 | 不变 |
| 灾备恢复 | RPO < 5min, RTO < 15min (演练验证) | 原 RPO<1s/RTO<1min → 更合理的内部平台标准 |
| 成本效率 | Dev 环境月均成本降低 50% | 原全面降低 30% → 聚焦 Dev 环境 |

---

## 6. 技术债务管理策略

### 6.1 各阶段技术债务预算

| 阶段 | 债务预算 | 重点领域 | Phase 2 实际经验 |
|------|---------|---------|----------------|
| Phase 1 | 15% 工时 | 允许简化的错误处理、基础测试覆盖。MVP 速度优先，但不可跳过架构分层 | 实际偿还: 24 项变更积压中 19 项在 Phase 2 内完成 |
| Phase 2 | 20% 工时 | 偿还 Phase 1 简化项；完善 EventBus 可靠性；补充集成测试 | 实际: 五维度审查 + S0-S2 全部修复 + 1427 测试 |
| Phase 3 | **25% 工时** | AgentCore P2/P3 集成；CI/CD 完善；Secrets 统一；监控体系 | **上调**: Phase 2 遗留 S4 变更 + P2/P3 集成工作量超预期 |
| Phase 4 | 15% 工时 | 架构审查和微调；文档完善；自动化运维工具 | - |

### 6.2 重构窗口期

每个阶段的最后 2 周为重构窗口期:
- 回顾本阶段产生的技术债务清单
- 评估对下一阶段的影响程度
- 执行高优先级重构任务
- 更新架构决策记录 (ADR)

### 6.3 架构演进路径

```
Phase 1: Modular Monolith (单体部署, boto3 Converse API)           ✅ 完成
   ↓ 模块边界已通过 DDD + EventBus 清晰定义
Phase 2: Platform API (ECS Fargate) + Agent 执行 (AgentCore Runtime)  ✅ 完成 ← ADR-006
   ↓ Claude Agent SDK + IAgentRuntime 接口抽象 + P0/P1 完成
Phase 2→3 过渡: AgentCore P2 集成 (Gateway 工具同步 + Memory MCP + OTEL)  ← M7-prep
   ↓ 运维基础完善 (CI/CD + Secrets + 监控)
Phase 3: 多 Agent 编排 (Claude Agent SDK 子 Agent + AgentCore A2A)
   ↓ orchestration + evaluation 模块
Phase 4: 平台成熟 (audit + insights 增强 + 自助构建器)
```

**关键原则**: Platform API 层保持 Modular Monolith 部署；Agent 执行层通过 AgentCore Runtime 独立部署和扩展。两者通过 `invoke_agent_runtime()` API 通信。拆分决策基于 ADR-006 和实际负载数据。

**Phase 2 经验新增原则**:
- **部署即验证**: 每个模块完成后尽早部署到真实环境验证（Phase 2 在 M6 后才首次部署，发现大量兼容性问题）
- **MySQL-First 测试**: 集成测试必须同时覆盖 MySQL，不能仅依赖 SQLite
- **基础镜像统一**: 所有 Docker 镜像统一使用 ECR Public 基础镜像 + AMD64 平台

---

## 7. 风险与依赖

### 7.1 关键技术风险

| 风险 | 影响 | 概率 | 缓解策略 | Phase 2 经验更新 |
|------|------|:----:|---------|----------------|
| Bedrock AgentCore API 变更 | execution/orchestration 模块需要适配 | 中 | Infrastructure 层适配器模式隔离 SDK 调用；关注 AWS re:Invent 发布 | `@aws-cdk/aws-bedrock-agentcore-alpha` 已验证可用；保留 L1 降级路径 |
| LLM 响应延迟不可控 | 用户体验下降，执行超时 | 高 | SSE 流式响应；异步执行 + 回调通知；超时降级策略 | 已实现: SSE + 滑动窗口 (C-S2-2) + 线程池 (C-S2-1) |
| RAG 检索质量不达标 | knowledge 模块价值受限 | 中 | 多种向量化策略对比评估；Hybrid Search (向量 + 关键词)；持续的评估反馈循环 | Bedrock KB 已集成 (ADR-005)；需 evaluation 模块进一步验证 |
| Multi-Agent 编排复杂度 | orchestration 模块开发周期超预期 | **高** | 先实现简单串行编排，逐步支持并行和条件分支；参考成熟开源框架设计 | **上调**: Claude Agent SDK 子 Agent + A2A 协议组合未经生产验证，需预留缓冲 |
| 前端可视化编排器性能 | 大型 DAG 渲染卡顿 | 低 | 虚拟化渲染；Canvas 替代 DOM 方案评估；限制单工作流节点数 | - |
| **MySQL 方言兼容性** (新增) | 迁移脚本或 ORM 查询在 MySQL 上失败 | **中** | MySQL 集成测试覆盖；TEXT 列无默认值；显式 session commit | Phase 2 实际遇到 5+ 方言差异问题 |
| **容器化部署陷阱** (新增) | ECS/AgentCore 容器启动失败 | **中** | 强制 AMD64 平台；ECR Public 镜像源；Agent Runtime 包含 Node.js 18+ | Phase 2 踩坑: ARM64、Docker Hub 限流、curl 不可用 |

### 7.2 外部依赖

| 依赖 | 影响范围 | 当前状态 | 备选方案 |
|------|---------|---------|---------|
| Amazon Bedrock AgentCore | execution, orchestration 模块 | GA (9 区域), boto3>=1.36.0 | Bedrock Converse API 降级路径 (ADR-003) |
| Claude Agent SDK | Agent 执行层 (唯一框架, ADR-006) | 正式版, 需 Node.js CLI 依赖 | BedrockLLMClient 降级到单轮对话 |
| AgentCore SDK (`bedrock-agentcore`) | Runtime 部署 | Python SDK 已发布 | 直接 boto3 调用 |
| Aurora MySQL 3.x | 全部关系数据存储 | 稳定可用 (ADR-005) | 标准 MySQL 8.0 (降级方案) |
| Bedrock Knowledge Bases | RAG 向量检索 (ADR-005) | GA | 自建 OpenSearch (降级方案 B) |
| AWS CDK 生态 | 全部基础设施 | 稳定 (>= 2.130) | 版本锁定 + 定期升级评估 |
| `@aws-cdk/aws-bedrock-agentcore-alpha` | AgentCore CDK 资源 | alpha (NPM 已发布) | L1 CfnResource 降级 |

### 7.3 团队依赖

| 依赖 | 阶段 | 说明 |
|------|------|------|
| 后端工程师 | Phase 1-4 | 核心开发力量，DDD 模块实现 |
| 前端工程师 | Phase 1-4 | FSD 架构实现，Phase 3 可视化编排器为关键挑战 |
| DevOps 工程师 | Phase 1 起 | CDK Stack 实现、CI/CD Pipeline、监控体系 |
| 产品经理 | Phase 2 起 | Agent 模板定义、用户反馈收集、市场策略 |
| 安全工程师 | Phase 4 | 审计合规模块评审、渗透测试 |

---

## 8. 规划调整总结与季度评审机制 (C-S3-3)

> **评审日期**: 2026-02-11 | **来源**: improvement-plan.md 产品审查 P1+P3+P10 | **决策记录**: ADR-007

### 8.1 本次调整总结

| 调整项 | 原规划 | 调整后 | 理由 |
|--------|--------|--------|------|
| 总体时间跨度 | 24 个月 | **18 个月** | AI 领域迭代快，长期规划易失效 |
| Phase 4 时间窗口 | 12-24 月 | **12-18 月** | 移除 marketplace 和多区域后工作量大幅缩减 |
| Phase 3 新增 M7-prep | 无 | 第 25-28 周 | P2 集成 + S4 运维基础需集中处理 |
| Phase 4 marketplace 模块 | 独立模块 | **移除** | 200 人内部平台无需市场机制 |
| Phase 4 analytics 模块 | 独立模块 | **降级为 insights 增强** | 避免过度工程化 |
| Phase 4 多区域部署 | CDK Pipeline 多区域 | **移除** | 内部平台用户量不支撑 ROI |
| 灾备指标 | RPO<1s, RTO<1min | **RPO<5min, RTO<15min** | 内部平台不需要金融级灾备 |
| Phase 3 活跃用户目标 | 50 人 | **20 人** | 初期推广更务实 |
| Phase 4 活跃用户目标 | 200 人 | **50 人** | 阶段性目标更务实 |
| Phase 3 技术债务预算 | 20% | **25%** | P2 遗留 S4 + AgentCore P2/P3 集成 |
| evaluation 模块 | 依赖 AgentCore Evaluations | **自建轻量框架** | AgentCore Evaluations 为预览版 |

### 8.2 规划模式调整

**从固定路线图 → 滚动规划**:

| 阶段 | 规划模式 | 说明 |
|------|---------|------|
| Phase 3 (当前) | **详细规划** — 里程碑拆解到周 | 明确的交付物和验收标准 |
| Phase 4 (下一阶段) | **方向性规划** — 季度目标 | 保留方向和核心模块，详细拆解待 Phase 3 末尾评审 |
| Phase 5+ (远期) | **愿景声明** — 年度方向 | 如需要，在 Phase 4 季度评审时决策 |

### 8.3 季度评审机制

**频率**: 每 12 周（约每季度）进行一次路线图评审。

**评审内容**:
1. **进度检查**: 对照里程碑完成情况
2. **经验教训**: 记录本季度踩坑和最佳实践
3. **外部变化**: AgentCore/Claude Agent SDK 版本更新、AWS 新服务发布
4. **用户反馈**: 核心团队使用体验和需求变化
5. **路线图调整**: 根据 1-4 调整下一季度详细规划

**评审产出**:
- 更新 `roadmap.md` 对应阶段
- 如有重大调整，创建 ADR
- 更新 `progress.md` 变更积压表

**下一次评审**: Phase 3 M7-prep 完成后 (约第 28 周)

---

## 附录: 模块与六大核心能力映射

| 核心能力 | 对应后端模块 | AgentCore 服务 | 首次交付阶段 | 调整说明 |
|---------|-------------|---------------|:----------:|---------|
| Agent 管理 | agents, templates | - | Phase 1/2 ✅ | - |
| 运行时引擎 | execution + IAgentRuntime | **AgentCore Runtime** + Claude Agent SDK | Phase 1/2 ✅ | P0+P1 已完成 |
| 工具集成 | tool-catalog | **AgentCore Gateway** (MCP) | Phase 2 ✅ / Phase 3 (P2-1) | 元数据管理 ✅；Gateway 工具同步待 M7-prep |
| 编排协作 | orchestration | AgentCore Runtime (A2A) | Phase 3 | 不变 |
| 记忆管理 | execution (Conversation/Message) | **AgentCore Memory** (MCP 桥接) | Phase 2 ✅ / Phase 3 (P2-2) | MySQL 会话管理 ✅；Memory MCP 待 M7-prep |
| 监控评估 | insights, evaluation | **AgentCore Observability** (OTEL) | Phase 2 ✅ / Phase 3 (P2-3) | structlog ✅；OTEL 待 M7-prep |
| 知识库 | knowledge | **Bedrock Knowledge Base** | Phase 2 ✅ | ADR-005 |
| 用户权限 | auth, audit | AgentCore Identity (Phase 4) | Phase 1 ✅ / Phase 4 | Identity 集成推迟到 P3-3 |
| 平台基础 | shared | - | Phase 1 ✅ | ~~marketplace~~、~~analytics~~ 已移除/降级 |
