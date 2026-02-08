# 四阶段迭代路线图

> **文档类型**: 战略规划 | **维护者**: 后端架构师 | **状态**: 初始版本

---

## 1. 路线图概述

### 1.1 四阶段总览

```
Phase 1: MVP 基础        Phase 2: 核心功能        Phase 3: 生态扩展        Phase 4: 企业成熟
   (0-3 月)                 (3-6 月)                (6-12 月)               (12-24 月)
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
  Database              Staging 环境            Prod 环境              灾备方案
  基础 CI/CD                                    蓝绿部署
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
| 4 | `execution` | 任务执行引擎 - 单 Agent 对话执行、Bedrock AgentCore 集成、SSE 流式响应 | shared, auth, agents |

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
| **ComputeStack** | ECS Fargate Service (后端 API)、ALB、Auto Scaling | 容器化部署 |
| **ApiStack** | API Gateway、WAF 规则、访问日志 | API 入口层 |

新增 Staging 环境，资源配置参考环境矩阵 (db.t3.medium 多 AZ)。集成 CloudWatch 监控 (日志组、基础告警)。

### 3.5 关键里程碑

| 里程碑 | 时间窗口 | 交付物 |
|--------|---------|--------|
| **M4: 工具目录** | 第 13-16 周 | tool-catalog 模块完成；MCP Server 注册与审批流程；前端工具目录界面 |
| **M5: 知识库 + 业务洞察** | 第 17-20 周 | knowledge 模块 (RAG 集成)；insights 模块 (成本归因/使用趋势)；前端仪表板 |
| **M6: 模板生态** | 第 21-24 周 | templates 模块 + 10 个预置模板；ComputeStack + ApiStack 部署 Staging |

### 3.6 验收标准

| 指标 | 目标值 |
|------|--------|
| Agent 模板数量 | >= 10 个覆盖常见业务场景 |
| 核心团队活跃用户 | >= 5 人日常使用 |
| API 可用性 | >= 99% (Staging 环境) |
| 单元测试覆盖率 | >= 85% (后端)、>= 80% (前端) |
| 知识库检索准确率 | Top-5 召回率 >= 80% |
| 成本归因覆盖率 | 所有 Agent 执行均有按团队/项目维度的成本归因 |

---

## 4. Phase 3: 生态扩展 (6-12 月)

### 4.1 目标

实现 Multi-Agent 编排能力，平台向全公司推广使用。

### 4.2 后端模块实现顺序

| 顺序 | 模块 | 职责 | 依赖 |
|:----:|------|------|------|
| 9 | `orchestration` | Multi-Agent 工作流编排 - DAG 定义/执行引擎、Agent 间消息路由、并行/串行执行策略 | shared, auth, agents, execution, tool-catalog |
| 10 | `evaluation` | Agent 质量评估 - 消费 AgentCore Evaluations 评估数据、自定义业务评估指标、评估报告可视化 | shared, auth, agents, execution, insights |

`orchestration` 优先于 `evaluation`，因为 Multi-Agent 编排是本阶段核心差异化能力。模型选择策略和 fallback 配置已合并到 `agents` 模块的 AgentConfig 中（Bedrock 原生提供多模型路由），不再作为独立模块。

### 4.3 前端功能

| 功能模块 | 关键页面/组件 |
|---------|-------------|
| 可视化编排器 | OrchestrationEditorPage (拖拽式 DAG 编辑器)、NodePalette (Agent/Tool 节点面板)、FlowCanvas (画布)、ConnectionLine |
| 评估报告 | EvaluationDashboardPage (评估结果总览)、TestCaseRunner (测试执行)、ScoreRadarChart |

### 4.4 基础设施

| CDK Stack | 变更 | 说明 |
|-----------|------|------|
| **MonitoringStack** | 增强: CloudWatch Dashboards、SNS 告警通知、X-Ray 分布式追踪 | 全链路可观测 |
| **ComputeStack** | 增强: 蓝绿部署 (CodeDeploy)、Auto Scaling 策略优化 | 零停机部署 |
| **Prod 环境** | 全量 Stack 部署: db.r6g.large 多 AZ、每 AZ 一个 NAT Gateway | 生产就绪 |

### 4.5 关键里程碑

| 里程碑 | 时间窗口 | 交付物 |
|--------|---------|--------|
| **M7: Multi-Agent 编排** | 第 25-32 周 | orchestration 模块完成；可视化编排器 MVP；支持串行/并行/条件分支 |
| **M8: 评估体系** | 第 33-40 周 | evaluation 模块 + 自动化评估 Pipeline；Agent 模型配置增强（fallback 策略） |
| **M9: 生产部署** | 第 41-48 周 | Prod 环境部署；蓝绿部署验证；全公司推广启动 (目标 50+ 活跃用户) |

### 4.6 验收标准

| 指标 | 目标值 |
|------|--------|
| 编排工作流支持 | 串行、并行、条件分支三种模式 |
| 全公司活跃用户 | >= 50 人 |
| API 可用性 | >= 99.5% (Prod 环境) |
| 部署成功率 | >= 99% (蓝绿部署) |
| Agent 评估覆盖率 | 所有公开模板均有基线评估分数 |
| P95 响应延迟 | < 300ms (非 LLM 接口) |

---

## 5. Phase 4: 企业成熟 (12-24 月)

### 5.1 目标

平台成熟化，实现自助式使用，降低 Agent 创建和管理门槛。

### 5.2 后端模块实现顺序

| 顺序 | 模块 | 职责 | 依赖 |
|:----:|------|------|------|
| 12 | `audit` | 审计日志与合规 - 全操作审计追踪、合规报告生成、数据保留策略 | shared, auth (全模块事件订阅) |
| 13 | `marketplace` | Agent 市场/分享 - Agent 发布/审核流程、版本管理、评价系统 | shared, auth, agents, templates, evaluation |
| 14 | `analytics` | 使用分析与洞察 - 用户行为分析、Agent 使用热力图、ROI 计算 | shared, auth, insights, execution |

`audit` 优先实现，因为企业级合规是全公司大规模使用的前提条件。`marketplace` 依赖 `evaluation` 提供的质量评分，`analytics` 依赖 `insights` 的数据积累。

### 5.3 前端功能

| 功能模块 | 关键页面/组件 |
|---------|-------------|
| Agent 市场 | MarketplacePage (Agent 浏览/搜索/评分)、PublishAgentForm (发布流程)、ReviewQueue (审核) |
| 高级分析看板 | AnalyticsDashboardPage (使用趋势)、ROICalculator、HeatmapChart、UserBehaviorFlow |
| 自助式 Agent 构建器 | AgentBuilderPage (低代码拖拽构建)、PromptEditor (提示词编辑器)、PreviewPanel (实时预览) |

### 5.4 基础设施

| 能力 | 实现方案 | 说明 |
|------|---------|------|
| **多区域部署** | CDK Pipeline + 多区域 Stack 实例化 | 降低跨区域访问延迟 |
| **灾备方案** | Aurora Global Database + S3 跨区域复制 + Route53 故障转移 | RPO < 1s, RTO < 1min |
| **成本优化自动化** | AWS Budgets 告警 + Compute Savings Plans + S3 智能分层 + Dev 环境定时缩减 | 目标: 整体成本降低 30% |

### 5.5 关键里程碑

| 里程碑 | 时间窗口 | 交付物 |
|--------|---------|--------|
| **M10: 审计合规** | 第 49-56 周 | audit 模块完成；全操作审计追踪；合规报告自动生成 |
| **M11: Agent 市场** | 第 57-72 周 | marketplace 模块完成；Agent 发布/审核流程；低代码 Agent 构建器 |
| **M12: 分析与优化** | 第 73-96 周 | analytics 模块完成；多区域部署；灾备方案验证；成本优化自动化 |

### 5.6 验收标准

| 指标 | 目标值 |
|------|--------|
| 全公司活跃用户 | >= 200 人 |
| Agent 市场发布数 | >= 50 个通过审核的 Agent |
| 自助创建比例 | >= 60% 的 Agent 由非技术人员自助创建 |
| API 可用性 | >= 99.9% (Prod 环境) |
| 审计覆盖率 | 100% 写操作有审计日志 |
| 灾备恢复 | RPO < 1s, RTO < 1min (演练验证) |
| 成本效率 | 单用户月均成本降低 30% (相比 Phase 3) |

---

## 6. 技术债务管理策略

### 6.1 各阶段技术债务预算

| 阶段 | 债务预算 | 重点领域 |
|------|---------|---------|
| Phase 1 | 15% 工时 | 允许简化的错误处理、基础测试覆盖。MVP 速度优先，但不可跳过架构分层 |
| Phase 2 | 20% 工时 | 偿还 Phase 1 简化项；完善 EventBus 可靠性 (Outbox Pattern)；补充集成测试 |
| Phase 3 | 20% 工时 | 性能优化 (数据库索引、缓存策略)；API 版本管理规范化；前端组件库规范化 |
| Phase 4 | 15% 工时 | 架构审查和微调；文档完善；自动化运维工具 |

### 6.2 重构窗口期

每个阶段的最后 2 周为重构窗口期:
- 回顾本阶段产生的技术债务清单
- 评估对下一阶段的影响程度
- 执行高优先级重构任务
- 更新架构决策记录 (ADR)

### 6.3 架构演进路径

```
Phase 1: Modular Monolith (单体部署)
   ↓ 模块边界已通过 DDD + EventBus 清晰定义
Phase 2: Modular Monolith (容器化部署, ECS Fargate)
   ↓ 如果特定模块有独立扩展需求
Phase 3: 可选微服务拆分 (execution/orchestration 模块独立部署)
   ↓ 基于实际负载数据决策
Phase 4: 混合架构 (核心单体 + 高负载模块微服务化)
```

**关键原则**: 不预设微服务拆分时间点。DDD 模块隔离确保了随时可拆分的能力，但只有当监控数据证明单模块成为瓶颈时才执行拆分。

---

## 7. 风险与依赖

### 7.1 关键技术风险

| 风险 | 影响 | 概率 | 缓解策略 |
|------|------|:----:|---------|
| Bedrock AgentCore API 变更 | execution/orchestration 模块需要适配 | 中 | Infrastructure 层适配器模式隔离 SDK 调用；关注 AWS re:Invent 发布 |
| LLM 响应延迟不可控 | 用户体验下降，执行超时 | 高 | SSE 流式响应；异步执行 + 回调通知；超时降级策略 |
| RAG 检索质量不达标 | knowledge 模块价值受限 | 中 | 多种向量化策略对比评估；Hybrid Search (向量 + 关键词)；持续的评估反馈循环 |
| Multi-Agent 编排复杂度 | orchestration 模块开发周期超预期 | 中 | 先实现简单串行编排，逐步支持并行和条件分支；参考成熟开源框架设计 |
| 前端可视化编排器性能 | 大型 DAG 渲染卡顿 | 低 | 虚拟化渲染；Canvas 替代 DOM 方案评估；限制单工作流节点数 |

### 7.2 外部依赖

| 依赖 | 影响范围 | 当前状态 | 备选方案 |
|------|---------|---------|---------|
| Amazon Bedrock AgentCore | execution, orchestration 模块 | 依赖 GA 版本稳定性 | Claude Agent SDK 独立部署（ECS/Docker，不经过 AgentCore Runtime） |
| Aurora MySQL 3.x | 全部数据存储 | 稳定可用 | 标准 MySQL 8.0 (降级方案) |
| Claude Agent SDK | Agent 执行核心 | 关注 SDK 版本更新 | Bedrock Converse API 作为降级路径 |
| AWS CDK 生态 | 全部基础设施 | 稳定 (>= 2.130) | 版本锁定 + 定期升级评估 |

### 7.3 团队依赖

| 依赖 | 阶段 | 说明 |
|------|------|------|
| 后端工程师 | Phase 1-4 | 核心开发力量，DDD 模块实现 |
| 前端工程师 | Phase 1-4 | FSD 架构实现，Phase 3 可视化编排器为关键挑战 |
| DevOps 工程师 | Phase 1 起 | CDK Stack 实现、CI/CD Pipeline、监控体系 |
| 产品经理 | Phase 2 起 | Agent 模板定义、用户反馈收集、市场策略 |
| 安全工程师 | Phase 4 | 审计合规模块评审、渗透测试 |

---

## 附录: 模块与六大核心能力映射

| 核心能力 | 对应后端模块 | 首次交付阶段 |
|---------|-------------|:----------:|
| Agent 管理 | agents, templates | Phase 1/2 |
| 运行时引擎 | execution, tool-catalog | Phase 1/2 |
| 编排协作 | orchestration | Phase 3 |
| 监控评估 | insights, evaluation | Phase 2/3 |
| 用户权限 | auth, audit | Phase 1/4 |
| 平台基础 | shared, knowledge, marketplace, analytics | Phase 1/2/3/4 |
