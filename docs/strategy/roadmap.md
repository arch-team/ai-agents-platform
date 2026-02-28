# 四阶段迭代路线图

> **文档类型**: 战略规划 | **维护者**: 后端架构师 | **状态**: v1.4 — M8.5 完成后环境策略简化 (移除 Staging)

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

Phase 5: Agent 驱动的企业智能
   (18-30 月) 🔄
┌──────────────────┐
│ 自动化评估 Pipeline │
│ 对话式 Agent Builder│
│ 多租户规模运营    │
└──────────────────┘

后端模块:
  evaluation 扩展 (M13 ✅)
  builder (M14)
  billing (M15)
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

~~新增 Staging 环境~~ (v1.4 移除: Dev+Prod 两套环境足够)。集成 CloudWatch 监控 (日志组、基础告警)。AgentCore CDK 使用 `@aws-cdk/aws-bedrock-agentcore-alpha` L2 Construct。

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

## 4. Phase 3: 生态扩展 (6-12 月) — M7 ✅ + M8 ✅ + M8.5 ✅ + M9 ✅

### 4.1 目标

实现 Multi-Agent 编排能力，完成前端 MVP，平台向核心团队推广。

> **调整说明 v1.2** (C-S3-3): 原规划假设 Phase 2 结束时 AgentCore 集成已完成，但实际 P0+P1 完成后 P2/P3 仍有 6 项未完成。Phase 3 需同时完成 AgentCore 深度集成 + orchestration 模块。
>
> **调整说明 v1.3** (ADR-009): M7 通过 Agent Teams (ADR-008) 替代 DAG 引擎完成，orchestration 模块正式取消。节省的容量投入前端 MVP 开发 (M8.5)。evaluation 模块精简为 MVP 范围。

### 4.2 Phase 3 就绪度评估 — 已更新 (ADR-009)

Phase 3 核心依赖项 **全部就绪**：

| 依赖项 | 状态 | 完成时间 |
|--------|:----:|---------|
| AgentCore Runtime | ⚠️ CDK 已部署 (2 AZ)，无容器运行 — 待 P3-4 构建推送 | M7-prep (CDK) |
| AgentCore Gateway | ✅ 已部署 (MCP) | M7-prep |
| AgentCore Gateway 集成 (P2-1) | ✅ 已完成 | M7-prep |
| AgentCore Memory (P2-2) | ✅ 已完成 | M7-prep |
| OpenTelemetry (P2-3) | ✅ 已完成 | M7-prep |
| Claude Agent SDK + Agent Teams | ✅ 已完成 | M7 (ADR-008) |
| CI/CD Pipeline (C-S4-1) | ✅ 已完成 | M7-prep |
| Secrets 管理统一 (C-S4-3) | ✅ 已完成 | M7-prep |
| 基础监控告警 (C-S4-4) | ✅ 已完成 | M7-prep |

**结论**: 技术依赖全部清零。当前阻塞因素是**前端缺失**（66+ 后端端点，零 UI）。

### 4.3 后端模块实现顺序 — 已更新 (ADR-009)

| 顺序 | 模块 | 职责 | 依赖 | 调整说明 |
|:----:|------|------|------|---------|
| ~~9~~ | ~~`orchestration`~~ | ~~DAG 定义/执行引擎~~ | - | **取消 (ADR-008)**: Agent Teams 替代，已在 execution 模块实现 |
| 9 | `evaluation` | Agent 质量评估 - 测试集定义 + 批量执行 + 基础评分。**MVP 范围**: 不含评估 Pipeline 自动化 | shared, auth, agents, execution | **精简 (ADR-009)**: 缩减范围，节省容量投入前端 |

**调整理由**: orchestration 被 Agent Teams 替代 (ADR-008)，无需独立模块。evaluation 精简为 MVP，节省的容量投入前端 MVP 开发。

### 4.4 前端功能 — 已更新 (ADR-009)

| 功能模块 | 关键页面/组件 | 调整说明 |
|---------|-------------|---------|
| ~~可视化编排器~~ | ~~DAG 编辑器~~ | **取消**: 随 orchestration 模块取消 |
| **核心用户流程 (M8.5 新增)** | LoginPage、DashboardPage、AgentListPage、AgentDetailPage、ChatPage、TeamExecutionPage | **新增**: 前端 MVP，覆盖 Phase 1-3 全部后端能力 |
| **工具/知识库管理** | ToolCatalogPage、KnowledgeBasePage、FileUploadWidget | 从 Phase 2 前端规划平移 |
| 评估报告 (精简) | EvaluationListPage、TestCaseForm | 精简为列表 + 表单，移除复杂图表 |

### 4.5 基础设施

| CDK Stack | 变更 | 说明 | 调整说明 |
|-----------|------|------|---------|
| **MonitoringStack** | 新增: OpenTelemetry (ADOT) + CloudWatch Dashboards + SNS 告警 | 全链路可观测 (P2-3 + C-S4-4) | **前移**: 从 Phase 3 中期前移到 M7 之前，作为 AgentCore P2 集成的一部分 |
| **ComputeStack** | 增强: Auto Scaling 策略优化 | ECS 滚动更新部署 | **简化 (v1.4)**: 蓝绿部署推迟到 Phase 4，初期 ECS 滚动更新足够 |
| ~~**Staging 环境**~~ | ~~完整 Prod 配置验证~~ | - | **移除 (v1.4)**: 内部平台 Dev+Prod 两套环境足够，Staging 成本高于收益 |
| **Prod 环境** | 全量 Stack 部署: db.r6g.large 多 AZ、每 AZ 一个 NAT Gateway、HTTPS + 域名 | 生产就绪 | **简化 (v1.4)**: Dev 承担预发布验证职责，`cdk diff` 审查后直接部署 Prod |

### 4.6 关键里程碑 — v1.3 (ADR-009)

| 里程碑 | 时间窗口 | 交付物 | 状态/调整 |
|--------|---------|--------|---------|
| **M7-prep** | 第 25-28 周 | P2-1/P2-2/P2-3 + S4-1/S4-3/S4-4 | ✅ 已完成 |
| **M7** | 第 29-36 周 | Agent Teams (ADR-008) — 替代 orchestration 模块 | ✅ 已完成 (13/13 任务) |
| **M8: 评估体系 (精简)** | 第 37-40 周 (4 周) | evaluation 模块 MVP: 测试集 CRUD + 批量执行 + 基础评分 | **缩短**: 6→4 周，移除评估 Pipeline 自动化 |
| **M8.5: 前端 MVP** | 第 41-48 周 (8 周) | 前端 React+TS+FSD: 登录 + Agent 管理 + 对话 + 团队执行 + 工具/知识库 | **新增**: 前端零到一，覆盖 Phase 1-3 后端全部核心能力 |
| **M9: 生产部署** | 第 49-52 周 (2-3 周) | CDK Prod 参数化 → `cdk diff` 审查 → Prod 部署 + HTTPS/域名 + 核心团队试用 (目标 10+ 用户) | **再简化 (v1.4)**: 移除 Staging，Dev 承担验证；蓝绿部署推迟；2-3 周完成 |

### 4.7 验收标准 — v1.3 (ADR-009)

| 指标 | 目标值 | 调整说明 |
|------|--------|---------|
| ~~编排工作流支持~~ | ~~串行/并行/条件分支~~ | **替换**: Agent Teams 自主编排 (ADR-008) ✅ 已达成 |
| Multi-Agent 协作 | Agent Teams 支持团队创建/任务分配/进度追踪 | 新增 (ADR-009) ✅ 已达成 |
| 核心团队活跃用户 | >= 10 人 | 原 20 人 → 10 人 (ADR-009: 前端新上线初期) |
| 前端功能覆盖 | 登录 + Agent 管理 + 对话 + 团队执行 | 新增 (ADR-009: 替换 DAG 编辑器) |
| API 可用性 | >= 99.5% (Prod 环境) | 不变 |
| Agent 评估覆盖率 | >= 3 个核心模板有基线评估 | 原"所有公开模板" → 3 个核心 (ADR-009: 评估精简) |
| P95 响应延迟 | < 300ms (非 LLM 接口) | 不变 |
| AgentCore P2 集成 | Gateway + Memory + OTEL 全部完成 | ✅ 已达成 |
| 运维成熟度 | CI/CD + Secrets + 监控告警全部就位 | ✅ 已达成 |
| 环境策略 | Dev (开发+验证) + Prod (生产) 两套环境 | **简化 (v1.4)**: 移除 Staging，降低运维成本 |

---

## 5. Phase 4: 企业成熟 (12-18 月) — v1.5 详细规划

> **调整说明 v1.5** (Phase 4 季度评审, 2026-02-13): 基于四维度评审（代码审计 + 外部技术变化 + Phase 3 经验教训 + 路线图拆解），Phase 4 从方向性规划升级为详细规划。核心调整：新增 M10-prep（执行层分离 + 技术基线升级）；M10 后端 audit + 前端覆盖度补全并行；自助 Agent 构建器降级为体验优化（前端覆盖度更紧迫）；14 项新变更积压注入。

### 5.1 目标

平台成熟化，完善合规审计和使用分析，支撑全公司推广使用。

**v1.5 补充目标**:
- 完成 Agent 执行层部署分离（P3-4/P3-5），实现 Platform API 与 AgentCore Runtime 架构解耦
- 前端覆盖度从 45% 提升到 85%+，补全缺失的 5 个核心页面
- 外部依赖全量升级（SDK 包名 + CDK alpha + Aurora），技术基线对齐最新版本

### 5.2 后端模块实现顺序

| 顺序 | 模块 | 职责 | 依赖 | 调整说明 |
|:----:|------|------|------|---------|
| 11 | `audit` | 审计日志与合规 - 全操作审计追踪、合规报告生成、数据保留策略 | shared, auth (全模块事件订阅) | 不变 |
| ~~12~~ | ~~`marketplace`~~ | ~~Agent 市场/分享~~ | - | **移除**: 200 人内部平台无需市场机制；模板分享通过 templates 模块已满足 |
| ~~13~~ | ~~`analytics`~~ | ~~使用分析与洞察~~ | - | **降级**: 合并为 insights 模块增强（新增用户行为分析和 ROI 计算），不再独立建模块 |

`audit` 是本阶段唯一新建模块。Phase 2 的 `insights` 模块在本阶段增强（用户行为分析、ROI 计算），不单独建 `analytics` 模块。

### 5.3 前端功能 — v1.5 更新

| 功能模块 | 关键页面/组件 | 调整说明 |
|---------|-------------|---------|
| **前端覆盖度补全 (M10 并行)** | KnowledgePage、TemplatesPage、ToolCatalogPage、InsightsPage、EvaluationPage | **v1.5 新增**: Phase 3 教训 — 前端启动过晚是最大遗憾，5 个缺失页面必须在 M10 补齐 |
| 审计与合规 | AuditLogPage (审计日志查询)、ComplianceReportPage (合规报告) | 与 audit 模块同步开发 |
| 增强分析看板 | InsightsDashboardPage 增强 (用户行为分析、ROI 计算、使用趋势) | 原 analytics 降级为 insights 增强 |
| Agent 体验优化 (M11) | Prompt Editor 增强、配置向导、实时预览 | **v1.5 降级**: 原"自助式 Agent 构建器"降级为体验优化，前端覆盖度补全更紧迫 |

### 5.4 基础设施 — v1.5 更新

| 能力 | 实现方案 | 说明 | 调整说明 |
|------|---------|------|---------|
| **Agent 执行层分离 (M10-prep)** | P3-4 容器构建 + ECR 推送 + P3-5 调用路径切换 | Platform API → invoke_agent_runtime() → AgentCore Runtime | **v1.5 新增**: 前置到 M10 之前，Phase 3 教训 — 基础设施前置 |
| **外部依赖升级 (M10-prep)** | SDK 包名 `claude-agent-sdk` + CDK alpha BREAKING CHANGE 适配 + Aurora 3.10.3 | 技术基线对齐 | **v1.5 新增**: CDK alpha 有 User Pool Client 替换 |
| ~~**多区域部署**~~ | ~~CDK Pipeline 多区域~~ | - | **移除**: 内部平台用户量不支撑 ROI |
| **灾备方案** | Aurora 跨 AZ 高可用 + S3 版本管理 + 定期快照 | RPO < 5min, RTO < 15min | 不变 |
| **成本优化** | AWS Budgets 告警 + Dev 环境定时缩减 + Savings Plans 评估 | 目标: Dev 非工作时段成本降低 50% | **v1.5 细化**: "月均" → "非工作时段" |

### 5.5 关键里程碑 — v1.5 详细规划

| 里程碑 | 时间窗口 | 交付物 | 状态/调整 |
|--------|---------|--------|---------|
| **M10-prep: 执行层分离 + 技术基线** | 第 53-56 周 (4 周) | P3-4/P3-5 + SDK/CDK/Aurora 升级 + OTEL 修复 | **v1.5 新增**: Phase 3 教训 — 基础设施前置 |
| **M10: 审计合规 + 前端补全** | 第 57-64 周 (8 周) | audit 模块 (10 任务) + 前端 5 页面补全 (7 任务)；覆盖度 45% → 85% | **v1.5 调整**: 前后端并行（Phase 3 教训） |
| **M11: 平台成熟化** | 第 65-70 周 (6 周) | insights 增强 (ROI + 用户行为) + 灾备验证 + Agent 体验优化 + Opus 4.6 评估 | **v1.5 调整**: 自助构建器降级为体验优化 |
| **M12: 全公司推广 + 深度集成** | 第 71-76 周 (6 周) | P3-3 Identity + P3-1 Memory 策略 + 推广运营 (50+ 用户) + 性能调优 | 不变 |

### 5.6 验收标准 — v1.5 更新

| 指标 | 目标值 | 调整说明 |
|------|--------|---------|
| 全公司活跃用户 | >= 50 人 | 不变 |
| ~~Agent 市场发布数~~ | ~~>= 50 个~~ | 移除 — marketplace 已移除 |
| 自助创建比例 | >= 40% 的 Agent 由非技术人员自助创建 | 不变 |
| API 可用性 | >= 99.9% (Prod 环境) | 不变 |
| 审计覆盖率 | 100% 写操作有审计日志 | 不变 |
| 灾备恢复 | RPO < 5min, RTO < 15min (演练验证) | 不变 |
| 成本效率 | Dev 环境非工作时段成本降低 50% | **v1.5 细化**: "月均" → "非工作时段" |
| **前端覆盖度** | **>= 85% (13+ 页面覆盖全部后端模块)** | **v1.5 新增**: Phase 3 教训 |
| **执行层分离** | **AgentCore Runtime 部署运行 + 双路径可切换** | **v1.5 新增**: P3-4/P3-5 完成验证 |
| **后端测试** | **>= 85% 覆盖率 + 0 个被阻断测试** | **v1.5 新增**: 解决 OTEL 阻断 |
| **外部依赖** | **SDK/CDK/Aurora 全部更新到最新稳定版** | **v1.5 新增**: 技术基线对齐 |
| P95 响应延迟 | < 300ms (非 LLM 接口) | 不变 |
| AgentCore 深度集成 | Identity + Memory 长期策略完成 | 不变（M12 交付） |

### 5.7 Phase 3 经验教训 (2026-02-13 评审补充)

> 本节记录 Phase 3 开发过程中的关键经验，为 Phase 4 执行提供指导。

#### 关键成功经验

| 经验 | 说明 | Phase 4 应用 |
|------|------|-------------|
| SDK 能力优先于自建 | ADR-008 Agent Teams 替代 DAG 引擎，节省 6-8 周，代码量减半 | 评估 AgentCore Memory/Gateway L2 新能力，避免重复造轮子 |
| 季度评审机制有效 | v1.2/v1.3/v1.4 三次调整都产生正确决策 | 保持，下一次评审在 M11 完成后 |
| 变更积压管理 | 24 项 S0-S4 全部清零，穿插执行避免债务累积 | Phase 4 初始化 14 项新变更，继续 S0-S4 分级穿插 |
| TDD + 高覆盖率 | 1653 测试 94%+ 覆盖率，重构和 Bug 修复信心高 | 继续保持，audit 模块同样 TDD 先行 |

#### 关键教训

| 教训 | 影响 | Phase 4 对策 |
|------|------|-------------|
| 前端启动过晚 | Phase 3 后期才有 UI，用户目标从 20 降到 10 | M10 后端 audit + 前端 5 页面并行开发 |
| AgentCore Runtime 未实际部署 | CDK 已部署但"空转"，执行层未分离 | M10-prep 前置 P3-4/P3-5 |
| Token 经济性无预算控制 | Agent Teams ~800K tokens/次，仅有告警无硬限 | Phase 4 评估 ClaudeAgentAdapter 层预算控制 |

### 5.8 Phase 4 风险登记簿

| # | 风险 | 概率 | 严重度 | 缓解策略 | 关联里程碑 |
|---|------|:----:|:------:|---------|-----------|
| R1 | P3-4/P3-5 执行层分离遇阻 | 中 | 高 | 保留进程内执行降级路径；预留 2 周缓冲；分步切换 | M10-prep |
| R2 | CDK agentcore alpha BREAKING CHANGE 适配超预期 | 中 | 高 | 保留 L1 CfnResource 降级路径；锁定验证通过的版本 | M10-prep |
| R3 | 前端 5 页面并行与后端 audit 资源竞争 | 中 | 中 | 前后端明确分工，前端使用已有后端 API 不阻塞 | M10 |
| R4 | 50+ 用户并发性能瓶颈 | 中 | 高 | M12 压力测试；Runtime 分离后 Platform API 压力降低 | M12 |
| R5 | Agent Teams 实验特性 SDK 变更 | 低 | 高 | 锁定 SDK 版本；IAgentRuntime 接口隔离变更 | 全 Phase |
| R6 | Sonnet inference profile prompt caching 限制 | 中 | 低 | 确认 inference profile 的 prompt caching 支持情况，必要时改用标准调用；Sonnet 4 为 GA 模型无需申请；Haiku 保底 | M12 |
| R7 | AgentCore Identity 集成复杂度 | 中 | 中 | 渐进式集成：Gateway 认证 → Token Vault → 全量切换 | M12 |
| R8 | 全公司推广用户增长不达预期 | 中 | 中 | 梯度推广 10 → 30 → 50；培训+文档+onboarding 配套 | M12 |

---

## 6. Phase 5：Agent 驱动的企业智能 (18-30 月) — ✅ 已完成

> **状态**: ✅ 全部完成 (M13+M14+M15) | **规划日期**: 2026-02-21 | **验收日期**: 2026-02-27 | **设计文档**: `.claude/plans/2026-02-20-phase5-design.md`
> **方案**: 深度 AWS 集成（方案二）— 最大化杠杆 Bedrock/AgentCore/AWS Organizations 已有能力

### 6.1 目标

将平台从"可管理的工具"升级为"可自我优化的企业智能基础设施"：
- 自主化率：≥70% Agent 由非技术用户通过 Builder 自助创建
- 平台价值：月度 ROI 报告可量化（节省工时 × 部门均值工资）
- 技术成熟度：SLA 99.9%、所有新模板上线前 Eval 覆盖、部门资源完全隔离

### 6.2 后端模块实现顺序

| 顺序 | 模块 | 职责 | 依赖 |
|:----:|------|------|------|
| M13 | `evaluation` 扩展 | Eval Pipeline 自动化 + BedrockEvalAdapter + 模型对比 Dashboard | Bedrock Model Evaluation API |
| M14 | `builder` (新建) | 对话式 Agent Builder（MCP 驱动）+ `auth` 扩展（SSO/LDAP） | Claude Code MCP + AgentCore Gateway |
| M15 | `billing` (新建) | 多租户隔离 + 部门预算配额 + ROI 自动报告 | AWS Cost Explorer + Organizations |

### 6.3 基础设施

| 里程碑 | CDK 变更 | 说明 |
|--------|---------|------|
| M13 | EventBridge 定时规则 + IAM Eval 权限 + CloudWatch 质量面板 | 每日 02:00 UTC 自动触发核心模板回归 |
| M14 | SecurityStack SAML 参数 + LDAP SG 出站规则 + Gateway 工具发现 API | SSO/LDAP 认证集成 |
| M15 | BillingStack（新建）: OrganizationRole + AWS Budgets + Reports S3 | 跨 Account 成本聚合 |

### 6.4 关键里程碑

| 里程碑 | 时间窗口 | 核心交付 | 状态 | 验收指标 |
|--------|:-------:|---------|:----:|---------|
| **M13: 自动化评估** | 第 1-3 月 | Eval Pipeline + Bedrock Eval 集成 + 模型对比 Dashboard | ✅ 已完成 | ≥5 模板每日自动回归 |
| **M14: 生态扩展** | 第 4-6 月 | Builder MCP + SSO/LDAP | ✅ 已完成 | 非技术自主创建率 ≥70% |
| **M15: 规模运营** | 第 7-10 月 | billing + 部门隔离 + ROI 报告 | ✅ 已完成 | 每部门独立成本视图 |
| **Phase 5 验收** | 第 10 月末 | 季度评审 + 全量质量门控 | ✅ 已完成 | ruff✅ mypy✅ pytest(2071/88.29%)✅ 架构合规✅ |

### 6.5 验收标准

| 指标 | 目标值 |
|------|:------:|
| 非技术用户自助创建率 | **≥70%** |
| WAA（周活跃 Agent 数）增长 | **≥3× Phase 4** |
| API SLA（Prod 非 LLM 接口） | **99.9%** |
| 所有新模板上线前 Eval 覆盖 | **100%** |
| 部门资源完全隔离 | **100%** |
| 后端覆盖率 | **≥85%** |

### 6.6 Phase 4 经验教训 (2026-02-21 评审)

| 经验 | 说明 | Phase 5 应用 |
|------|------|-------------|
| Subagent 驱动开发效率高 | M13 10 任务通过 Subagent 驱动 + 双阶段 Review 完成 | M14/M15 继续使用此模式 |
| IRepository 方法名约定 | 项目实际用 create/update/get_by_id，非 save/get | 新仓储实现前必读现有 RepositoryImpl |
| MySQL TEXT 字段无 ORM default | mapped_column(Text, default=x) 在 MySQL 上触发约束问题 | 新模块建表规范中新增此检查项 |
| asyncio.to_thread 封装 boto3 | 标准模式，BedrockEvalAdapter 延续此模式 | 所有 AWS SDK 适配器均使用此模式 |

### 6.7 Phase 5 风险登记簿

| # | 风险 | 概率 | 严重度 | 缓解策略 |
|---|------|:----:|:------:|---------|
| R1 | Bedrock Model Evaluation API GA 早期接口变更 | 中 | 中 | 锁定版本 + BedrockEvalAdapter 隔离；保留手动评分降级路径 |
| R2 | Claude Code MCP 调用延迟影响 Builder 体验 | 中 | 中 | 异步生成 + SSE 流式；P95 < 5s 硬指标 |
| R3 | 企业 LDAP/SSO 配置复杂度超预期 | 中 | 高 | 先支持 SAML（标准化程度高）；LDAP 作为可选补充 |
| R4 | 部门隔离改造全量实体 department_id 迁移 | 高 | 高 | M15 前做 Alembic migration 预演；department_id 允许 NULL 渐进填充 |

---

## 7. Phase 6：平台智能化 (30-42 月) — v1.7 规划

> **状态**: 概要规划 | **规划日期**: 2026-02-27 | **方向**: 从"可管理的 Agent 平台"进化为"自主智能平台"

### 7.1 目标

将平台 Agent 能力从"工具执行者"升级为"有记忆、能协作、自主选择工具的智能体"：
- **记忆能力**: Agent 具备跨会话长期记忆，学习用户偏好和组织知识
- **协作智能**: 复杂任务自动分解为多 Agent 协作，无需人工配置团队
- **工具自治**: Agent 根据任务自主发现和选择最优工具组合

### 7.2 后端模块实现顺序

| 顺序 | 模块 | 职责 | 依赖 |
|:----:|------|------|------|
| M16 | `agents` + `tool_catalog` | Agent-Tool 绑定 (tool_ids) + Memory CRUD | IToolQuerier, IAgentQuerier |
| M17 | `execution` 协作扩展 | 智能编排引擎 + 协作模式 (Hierarchical/Pipeline) + 动态角色分配 | M16 (跨团队知识共享需 Memory) + Agent Teams |
| M18 | `tool_catalog` 智能扩展 | 工具推荐引擎 + Agent 自主工具选择 + 工具调用分析面板 | insights 模块 (调用数据) + tool_catalog |

### 7.3 基础设施

| 里程碑 | CDK 变更 | 说明 |
|--------|---------|------|
| M16 | AgentCore Memory 资源 + IAM 权限 + VPC Endpoint | Memory 持久化存储 |
| M17 | ECS 扩缩容策略调整 (Teams 并发) + CloudWatch 编排面板 | 多 Agent 并发执行资源保障 |
| M18 | 工具推荐 Lambda + 调用分析 CloudWatch Dashboard | 推荐引擎异步计算 |

### 7.4 关键里程碑

| 里程碑 | 时间窗口 | 核心交付 | 状态 | 验收指标 |
|--------|:-------:|---------|:----:|---------|
| **M16: Agent 工具绑定 + Memory** | 第 1-4 月 | Agent-Tool 绑定 + Memory CRUD + Memory MCP | 进行中 | Agent 工具执行成功率 >=90% |
| **M17: 智能协作引擎** | 第 5-8 月 | 协作模式扩展 + 任务自动分解 + 动态角色分配 | 待开始 | 复杂任务自动分解准确率 ≥70% |
| **M18: 工具智能化** | 第 9-12 月 | 工具推荐引擎 + 自主工具选择 + 调用分析面板 | 待开始 | 工具推荐采纳率 ≥60% |
| **Phase 6 验收** | 第 12 月末 | 季度评审 + 全量质量门控 | 待开始 | 综合验收标准全部达标 |

### 7.5 验收标准

| 指标 | 目标值 |
|------|:------:|
| Agent 跨会话记忆召回成功率 | **≥80%** |
| 复杂任务自动分解准确率 | **≥70%** |
| 工具推荐采纳率 | **≥60%** |
| API SLA（Prod 非 LLM 接口） | **99.9%** |
| 后端覆盖率 | **≥85%** |

### 7.6 Phase 5 经验教训 (2026-02-27 评审)

| 经验 | 说明 | Phase 6 应用 |
|------|------|-------------|
| Memory 接口先行，实现后补 | IMemoryService + MCP 封装已就绪但无实现 | M16 直接基于已有接口补齐，减少改动面 |
| Agent Teams 实验性特性风险 | 依赖 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | M17 关注 SDK 升级，Teams GA 后移除实验标记 |
| 工具系统 Gateway 同步成熟 | GatewaySyncAdapter + 事件驱动已稳定运行 | M18 在此基础上叠加推荐层，不动核心同步链路 |
| CLIConnectionError 重试模式 | 已验证有效，提升 Agent 执行稳定性 | Phase 6 新适配器延续此重试模式 |

### 7.7 Phase 6 风险登记簿

| # | 风险 | 概率 | 严重度 | 缓解策略 |
|---|------|:----:|:------:|---------|
| R1 | AgentCore Memory API 接口不稳定 (预览期) | 中 | 高 | IMemoryService 接口隔离；保留 session 级内存降级方案 |
| R2 | 智能编排 Token 消耗过高 | 高 | 中 | 任务分解模型使用 Haiku (低成本)；billing 模块预算控制联动 |
| R3 | 工具推荐冷启动问题 (缺少历史调用数据) | 中 | 中 | 基于工具描述相似度的规则引擎作为启动方案；渐进切换到 ML 推荐 |
| R4 | claude-agent-sdk Teams 特性 Breaking Change | 低 | 高 | 锁定 SDK 版本；升级前做回归测试；ClaudeAgentAdapter 隔离变更 |

### 7.8 技术决策待定

| 决策点 | 选项 | 预计时间 |
|--------|------|---------|
| Memory 存储后端 | AgentCore Memory vs 自建 (DynamoDB/Redis) | M16 启动前 |
| 编排模型选择 | Claude Haiku (低成本) vs Sonnet (高精度) | M17 启动前 |
| 推荐引擎架构 | 规则引擎 vs ML 模型 vs Hybrid | M18 启动前 |

---

## 8. 技术债务管理策略

### 8.1 各阶段技术债务预算

| 阶段 | 债务预算 | 重点领域 | Phase 2 实际经验 |
|------|---------|---------|----------------|
| Phase 1 | 15% 工时 | 允许简化的错误处理、基础测试覆盖。MVP 速度优先，但不可跳过架构分层 | 实际偿还: 24 项变更积压中 19 项在 Phase 2 内完成 |
| Phase 2 | 20% 工时 | 偿还 Phase 1 简化项；完善 EventBus 可靠性；补充集成测试 | 实际: 五维度审查 + S0-S2 全部修复 + 1427 测试 |
| Phase 3 | **25% 工时** | AgentCore P2/P3 集成；CI/CD 完善；Secrets 统一；监控体系 | **上调**: Phase 2 遗留 S4 变更 + P2/P3 集成工作量超预期 |
| Phase 4 | **20% 工时** | P3-4/P3-5 执行层分离；前端覆盖度补全；外部依赖升级；14 项变更积压 | **上调**: Phase 3 遗留 P3 集成 + 前端补全 + 技术基线升级工作量超预期 |

### 8.2 重构窗口期

每个阶段的最后 2 周为重构窗口期:
- 回顾本阶段产生的技术债务清单
- 评估对下一阶段的影响程度
- 执行高优先级重构任务
- 更新架构决策记录 (ADR)

### 8.3 架构演进路径

```
Phase 1: Modular Monolith (单体部署, boto3 Converse API)           ✅ 完成
   ↓ 模块边界已通过 DDD + EventBus 清晰定义
Phase 2: Platform API (ECS Fargate) + Agent SDK 进程内执行             ✅ 完成 ← ADR-006
   ↓ Claude Agent SDK + IAgentRuntime 接口抽象 + P0/P1 完成
   ↓ 注: Agent 当前在 ECS Fargate 进程内通过 claude_agent_sdk.query() 直接执行
   ↓ AgentCore Runtime CDK 已部署 + agent_entrypoint.py 已就绪，但尚未连接 (P3-4/P3-5)
Phase 2→3 过渡: AgentCore P2 集成 (Gateway 工具同步 + Memory MCP + OTEL)  ← M7-prep ✅
   ↓ 运维基础完善 (CI/CD + Secrets + 监控) ✅
Phase 3: Agent Teams 多智能体协作 (ADR-008 替代 DAG 引擎) ← M7 ✅
   ↓ evaluation MVP + 前端 MVP (M8 + M8.5)
   ↓ Prod 部署 + 核心团队推广 (M9)
Phase 3→4 过渡 (M10-prep): 执行层部署分离 (P3-4 容器部署 + P3-5 调用路径切换)  ← 下一步
   ↓ SDK 包名更新 + CDK alpha 升级 + Aurora 3.10.3 + OTEL 修复
   ↓ Platform API 通过 invoke_agent_runtime() 委托 AgentCore Runtime 执行
Phase 4: 平台成熟 (audit + 前端补全 + insights 增强 + Identity/Memory + 推广 50+ 用户)
Phase 4→5 过渡 (2026-02-21): Phase 5 季度评审完成，M13 启动
Phase 5A: 自动化评估 (Bedrock Eval API + EvalPipeline 模块扩展) ← M13 ✅
Phase 5B: 生态扩展 (Claude MCP Builder + SSO/LDAP) ← M14 ✅
Phase 5C: 规模运营 (billing 模块 + 多租户 + AWS Organizations) ← M15 ✅
Phase 6A: Agent 记忆系统 (AgentCore Memory + 短期/长期分区 + Memory×KB 联动) ← M16
Phase 6B: 智能协作引擎 (Hierarchical/Pipeline 模式 + 任务自动分解 + 动态角色) ← M17
Phase 6C: 工具智能化 (推荐引擎 + 自主工具选择 + 调用分析面板) ← M18
```

**关键原则**: Platform API 层保持 Modular Monolith 部署；Agent 执行层目标是通过 AgentCore Runtime 独立部署和扩展，两者通过 `invoke_agent_runtime()` API 通信。当前 Agent 在 ECS Fargate 进程内执行（ClaudeAgentAdapter），AgentCore Runtime 部署分离待 P3-4/P3-5 完成。拆分决策基于 ADR-006 和实际负载数据。

**Phase 2 经验新增原则**:
- **部署即验证**: 每个模块完成后尽早部署到真实环境验证（Phase 2 在 M6 后才首次部署，发现大量兼容性问题）
- **MySQL-First 测试**: 集成测试必须同时覆盖 MySQL，不能仅依赖 SQLite
- **基础镜像统一**: 所有 Docker 镜像统一使用 ECR Public 基础镜像 + AMD64 平台

**v1.4 环境策略原则**:
- **Dev+Prod 两套环境**: 内部平台无需 Staging，Dev 承担开发+验证双重职责
- **`cdk diff` 审查替代 Staging**: Prod 部署前通过 `cdk diff` 审查配置差异，人工确认
- **渐进式运维升级**: 蓝绿部署等高级运维能力推迟到用户量增长后按需引入

---

## 9. 风险与依赖

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
| Claude Agent SDK | Agent 执行层 (唯一框架, ADR-006) | v0.1.35 (bundled CLI 2.1.39, 无需 Node.js); **包名改为 `claude-agent-sdk`** | BedrockLLMClient 降级到单轮对话 |
| AgentCore SDK (`bedrock-agentcore`) | Runtime 部署 | v1.3.0 (2026-02-11) | 直接 boto3 调用 |
| Aurora MySQL 3.x | 全部关系数据存储 | 3.10.0 → **3.10.3 待升级** (ADR-005) | 标准 MySQL 8.0 (降级方案) |
| Bedrock Knowledge Bases | RAG 向量检索 (ADR-005) | GA | 自建 OpenSearch (降级方案 B) |
| AWS CDK 生态 | 全部基础设施 | 稳定 (>= 2.130) | 版本锁定 + 定期升级评估 |
| `@aws-cdk/aws-bedrock-agentcore-alpha` | AgentCore CDK 资源 | 2.238.0-alpha.0 (**有 BREAKING CHANGE: User Pool Client 替换**) | L1 CfnResource 降级 |
| Claude Opus 4.6 | 高端 Agent 任务 (可选) | 2026-02-05 上线 Bedrock; 1M 上下文 + 自适应思考 | Claude Sonnet/Haiku (成本优化) |

### 7.3 团队依赖

| 依赖 | 阶段 | 说明 |
|------|------|------|
| 后端工程师 | Phase 1-4 | 核心开发力量，DDD 模块实现 |
| 前端工程师 | Phase 1-4 | FSD 架构实现，Phase 3 可视化编排器为关键挑战 |
| DevOps 工程师 | Phase 1 起 | CDK Stack 实现、CI/CD Pipeline、监控体系 |
| 产品经理 | Phase 2 起 | Agent 模板定义、用户反馈收集、市场策略 |
| 安全工程师 | Phase 4 | 审计合规模块评审、渗透测试 |

---

## 10. 规划调整总结与季度评审机制 (C-S3-3)

> **评审日期**: 2026-02-11 | **来源**: improvement-plan.md 产品审查 P1+P3+P10 | **决策记录**: ADR-007

### 10.1 本次调整总结

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
| Staging 环境 | 独立 Staging 环境 | **移除** | 内部平台 Dev+Prod 两套足够，Staging 成本高于收益 |
| 蓝绿部署 | M9 实现 CodeDeploy | **推迟到 Phase 4** | 初期 ECS 滚动更新足够，用户量小 |
| M9 周期 | 4 周 | **2-3 周** | 移除 Staging 后工作量缩减 |

### 10.2 规划模式调整

**从固定路线图 → 滚动规划**:

| 阶段 | 规划模式 | 说明 |
|------|---------|------|
| Phase 3 | **已完成** — 全部 4 个里程碑交付 | M7 + M8 + M8.5 + M9 ✅ |
| Phase 4 | **已完成** — M10-prep + M10 + M11 + M12 全部交付 | v1.5 季度评审后完成 |
| Phase 5 | **已完成** — M13/M14/M15 全部交付 + 验收通过 | v1.6 规划 + v1.7 验收 (2026-02-27) |
| Phase 6 (待规划) | **概念阶段** — 待 v1.7 季度评审确定方向 | v1.7 季度评审 (2026-02-27) 启动规划 |

### 10.3 季度评审机制

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

**下一次评审**: Phase 6 规划确定后 (待定)

**已完成评审**:
- v1.2 (2026-02-11): Phase 2 完成后 → ADR-007 (路线图调整)
- v1.3 (2026-02-12): M7 完成后 → ADR-009 (orchestration 取消, 前端提升优先级)
- v1.4 (2026-02-12): M8.5 完成后 → 环境策略简化 (移除 Staging, Dev+Prod 两套环境)
- v1.5 (2026-02-13): Phase 3 全部完成后 → Phase 4 季度评审 (四维度: 代码审计+技术变化+经验教训+路线图拆解; M10-prep 新增; 前后端并行; 14 项变更积压)
- v1.6 (2026-02-21): Phase 4 全部完成后 → Phase 5 季度评审（深度 AWS 集成方案批准；M13/M14/M15 详细规划；BedrockEvalAdapter + Builder MCP + billing 三阶段路线图）
- v1.7 (2026-02-27): Phase 5 全部完成后 → Phase 5 验收（代码质量门控: ruff✅ mypy(462文件)✅ pytest(2071/88.29%)✅ 4模块架构合规✅；运营指标待 Prod 数据收集）

---

## 附录: 模块与六大核心能力映射

| 核心能力 | 对应后端模块 | AgentCore 服务 | 首次交付阶段 | 调整说明 |
|---------|-------------|---------------|:----------:|---------|
| Agent 管理 | agents, templates | - | Phase 1/2 ✅ | - |
| 运行时引擎 | execution + IAgentRuntime | **AgentCore Runtime** + Claude Agent SDK | Phase 1/2 ✅ | P0+P1 已完成; 当前进程内执行, Runtime 部署分离待 P3-4/P3-5 |
| 工具集成 | tool-catalog | **AgentCore Gateway** (MCP) | Phase 2 ✅ / Phase 3 (P2-1) | 元数据管理 ✅；Gateway 工具同步待 M7-prep |
| 编排协作 | ~~orchestration~~ → execution (Agent Teams) | Claude Agent SDK Teams + AgentCore Runtime | Phase 3 ✅ | ADR-008: Agent Teams 替代 DAG 引擎 |
| 记忆管理 | execution (Conversation/Message) | **AgentCore Memory** (MCP 桥接) | Phase 2 ✅ / Phase 3 (P2-2) | MySQL 会话管理 ✅；Memory MCP 待 M7-prep |
| 监控评估 | insights, evaluation | **AgentCore Observability** (OTEL) | Phase 2 ✅ / Phase 3 (P2-3) | structlog ✅；OTEL 待 M7-prep |
| 知识库 | knowledge | **Bedrock Knowledge Base** | Phase 2 ✅ | ADR-005 |
| 用户权限 | auth, audit | AgentCore Identity (Phase 4) | Phase 1 ✅ / Phase 4 | Identity 集成推迟到 P3-3 |
| 平台基础 | shared | - | Phase 1 ✅ | ~~marketplace~~、~~analytics~~ 已移除/降级 |
