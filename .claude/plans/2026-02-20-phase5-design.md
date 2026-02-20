# Phase 5 设计文档：Agent 驱动的企业智能

> **状态**: 已批准 | **日期**: 2026-02-20 | **时间跨度**: 18-30 月（预计 10 个月）
> **方案**: 深度 AWS 集成（方案二）| **决策人**: 项目负责人

---

## 1. 定位与背景

Phase 5 是 `vision-mission.md` §2.2 第三阶段"Agent 驱动的企业智能"的具体落地。

**前置状态（Phase 4 出口）**：
- 平台已部署 Prod 环境，35→50+ 活跃用户
- M12 完成：AgentCore Identity/Memory/A2A + 审计合规 + 全公司推广
- 技术基线：DDD Modular Monolith + Clean Architecture + AgentCore 深度集成
- 变更积压：Phase 2-3 24/24 ✅ | Phase 4 19/19 ✅ | AgentCore P3 5/5 ✅

**Phase 5 核心命题**：将平台从"可管理的工具"升级为"可自我优化的企业智能基础设施"。

**选型理由（方案二：深度 AWS 集成）**：
- 遵循 SDK-First 原则，杠杆 Bedrock Model Evaluation API / AgentCore Gateway / AWS Organizations 已有能力
- 避免重复建设评估引擎、Builder 后端、成本管理基础设施
- 封装层保持 < 100 行，与现有适配器模式一致

---

## 2. 成功标准

| 维度 | 指标 | 目标值 |
|------|------|:------:|
| 自主化率 | 非技术用户通过 Builder 自助创建 Agent 比例 | **≥70%** |
| 平台价值 | 月度 ROI 报告可计算（节省工时 × 部门均值工资） | **可量化** |
| 平台价值 | WAA（周活跃 Agent 数）增长 | **≥3× Phase 4** |
| 技术成熟度 | API SLA（Prod 非 LLM 接口） | **99.9%** |
| 技术成熟度 | 所有新模板上线前 Eval 覆盖 | **100%** |
| 技术成熟度 | 部门资源完全隔离 | **100% 归属** |
| 测试质量 | 后端覆盖率 | **≥85%** |

---

## 3. 架构演进路径

```
Phase 4（当前基线）                Phase 5A          Phase 5B             Phase 5C
──────────────────────────────    ──────────────    ─────────────────    ────────────────────
Platform API (ECS Fargate)    →   + Eval Pipeline   + builder 模块        + billing 模块
AgentCore Runtime（分离执行）       + Bedrock Eval    + MCP 生成配置         + 多租户隔离
AgentCore Gateway（MCP 工具）       + OTEL 质量追踪   + SSO/LDAP 对接       + 多 Account 成本
AgentCore Memory（长期记忆）
Aurora MySQL + S3
```

**技术原则（继承 Phase 4）**：
- SDK-First 延伸：Eval / Builder / Cost 均优先调用 AWS GA API，封装层 < 100 行
- 接口抽象隔离：新增 `IEvalService` / `IBuilderService` / `ICostBudgetService` 三个跨模块接口
- 现有架构不破坏：新模块遵循现有 DDD 四层结构（`api/ → application/ → domain/ ← infrastructure/`）

---

## 4. Phase 5A：智能评估（第 1-3 月）里程碑 M13

### 4.1 目标

将 `evaluation` 模块从"手动创建测试集 + 人工查看结果"升级为自动化 Eval Pipeline，借助 Bedrock Model Evaluation API 提供跨模型对比，通过 AgentCore OTEL 数据驱动持续质量追踪。

### 4.2 能力对比

| 现有（Phase 3 MVP） | Phase 5A 扩展 |
|--------------------|--------------|
| 手动创建 TestSuite / TestCase | + 自动生成测试用例（基于历史对话） |
| 手动触发 EvaluationRun | + 定时 / 代码推送触发 Pipeline |
| 基础评分（准确率 / 相关性） | + Bedrock Model Evaluation API 评分 |
| 人工查看结果列表 | + Agent 版本对比 Dashboard |
| — | + OTEL Trace 驱动质量追踪 |

### 4.3 后端扩展（`evaluation` 模块）

| 层级 | 新增内容 |
|------|---------|
| Domain | `EvalPipeline` 实体 + `PipelineStatus` 状态机（SCHEDULED → RUNNING → COMPLETED） |
| Application | `EvalPipelineService`：触发 → 采集历史对话 → 调用 Bedrock Eval API → 存储结果 |
| Infrastructure | `BedrockEvalAdapter`（薄封装 `bedrock-agentcore` Eval API，< 100 行） |
| API | `POST /eval-pipelines`、`GET /eval-pipelines/{id}/compare` |

### 4.4 前端扩展（`EvaluationPage`）

- **Pipeline 视图**：触发方式（手动/定时）、运行状态、历史趋势折线图
- **模型对比视图**：同一 TestSuite 下 Haiku vs Sonnet vs Opus 的评分矩阵

### 4.5 基础设施

| 资源 | 变更 |
|------|------|
| IAM | 新增 `bedrock:CreateEvaluationJob` / `GetEvaluationJob` 权限 |
| EventBridge | 定时触发规则（每日 02:00 UTC 对核心模板跑回归） |
| CloudWatch | Eval 结果指标 → 质量 Dashboard 面板 |

### 4.6 验收标准

| 指标 | 目标 |
|------|------|
| Pipeline 自动化 | ≥5 个核心模板每日自动回归 |
| 模型对比覆盖 | 所有新模板上线前必须通过 Eval 对比 |
| 质量追踪延迟 | Eval 结果在执行完成后 5 分钟内可查 |
| 测试覆盖 | evaluation 模块覆盖率维持 ≥85% |

---

## 5. Phase 5B：生态扩展（第 4-6 月）里程碑 M14

### 5.1 目标

通过 MCP 协议驱动的可视化 Agent Builder + 企业 SSO/LDAP 对接，将非技术用户自助创建率从 40% 提升到 70%+。不重建 UI 拖拽引擎，让 Claude Code 通过 MCP 成为 Builder 的智能后端。

### 5.2 能力对比

| 现有（Phase 4） | Phase 5B 新路径 |
|----------------|----------------|
| 手填表单（系统提示词 + 模型 + 配置） | + 对话式 Builder：用自然语言描述需求 |
| 选择模板 → 手动调整参数 | + Claude via MCP 自动生成 Agent 配置草稿 |
| 无 SSO，需手动创建账号 | + 企业 SSO/LDAP：一键登录，自动映射角色 |
| AgentCore Gateway 手动注册工具 | + Gateway 工具发现：按部门自动推荐可用工具 |

### 5.3 新建 `builder` 模块

| 层级 | 内容 |
|------|------|
| Domain | `BuilderSession` 实体 + `BuilderMessage` 值对象；`IBuilderService` 接口 |
| Application | `BuilderService`：接收自然语言需求 → 调用 MCP Claude → 解析生成 `CreateAgentDTO` → 用户确认 → 调用 AgentService 创建 |
| Infrastructure | `ClaudeBuilderAdapter`（通过 MCP SSE 调用 Claude Code，封装 < 100 行）；`LdapAdapter`（对接企业 LDAP） |
| API | `POST /builder/sessions`、`POST /builder/sessions/{id}/messages`（SSE 流式）、`POST /builder/sessions/{id}/confirm` |

### 5.4 `auth` 模块扩展（SSO）

| 新增内容 | 说明 |
|---------|------|
| `SsoProvider` 枚举 | INTERNAL / SAML / LDAP |
| `SsoService` | SAML 2.0 SP 实现 + LDAP bind；映射企业组 → 平台 Role |
| `GET /auth/sso/callback` | SSO 回调端点 |

### 5.5 前端新页面

| 页面 | 内容 |
|------|------|
| `BuilderPage`（新建） | 对话式 Builder：左侧对话框 → 右侧实时预览 Agent 配置 → 底部确认创建 |
| `LoginPage` 扩展 | 新增"企业 SSO 登录"入口，保留原用户名/密码 |
| `AdminPage` 增强 | SSO 配置管理（SAML metadata 上传 / LDAP 连接测试） |

### 5.6 基础设施

| 资源 | 变更 |
|------|------|
| AgentCore Gateway | 新增 `list_tools_by_department` 封装，按部门 tag 过滤工具 |
| Secrets Manager | 新增 LDAP bind 密码、SAML SP 私钥存储 |
| ALB | 新增 `/auth/sso/*` 路由规则 |
| CDK | `SecurityStack` 新增 SAML IdP 元数据参数；`ComputeStack` 新增 LDAP SG 出站规则 |

### 5.7 验收标准

| 指标 | 目标 |
|------|------|
| 非技术用户自助创建率 | ≥70%（Wave 4 推广后 30 天内） |
| Builder 完成率 | ≥60% 的 Builder 会话最终确认创建 Agent |
| SSO 覆盖率 | 所有新用户通过 SSO 注册，无需手动创建账号 |
| Builder 响应延迟 | 首个配置草稿 P95 < 5s |

---

## 6. Phase 5C：规模运营（第 7-10 月）里程碑 M15

### 6.1 目标

引入部门级多租户隔离、成本预算硬限和 ROI 自动报告。深度对接 AWS Organizations + Cost Explorer，让成本数据从 AWS 账单直接流入平台治理层。

### 6.2 能力对比

| 现有（Phase 4 insights 模块） | Phase 5C 扩展 |
|-----------------------------|--------------|
| AWS Cost Explorer 全平台成本查询 | + 部门级预算配额（硬限 + 软警告） |
| estimated_cost 弃用，依赖 CE 真实账单 | + 多 AWS Account 成本聚合 |
| 按 Agent/用户维度归因 | + 预测性超额预警（7 天趋势预测） |
| 手动查看 InsightsPage | + 自动 ROI 报告（PDF，按周/月） |
| 无部门隔离 | + 部门命名空间隔离（Agent/工具/知识库） |

### 6.3 新建 `billing` 模块

| 层级 | 内容 |
|------|------|
| Domain | `Department` 聚合根（id, name, aws_account_id, budget_limit, alert_threshold）；`BudgetAlert` 实体；`IBudgetRepository` 接口 |
| Application | `BillingService`：查询部门消费 → 对比预算 → 触发告警；`RoiReportService`：聚合 WAA + 成本 + 节省工时 → 生成报告 |
| Infrastructure | `CostExplorerMultiAccountAdapter`（跨 Account 成本聚合，< 100 行）；`PdfReportGenerator`（reportlab 薄封装） |
| API | `GET /billing/departments/{id}/usage`、`POST /billing/budgets`、`GET /billing/reports/{type}` |

### 6.4 `auth` 模块扩展（部门命名空间）

| 新增内容 | 说明 |
|---------|------|
| `department_id` 字段 | User / Agent / Tool / KnowledgeBase 所有实体添加部门归属 |
| `DepartmentMiddleware` | 从 JWT claims 提取 department_id，注入请求上下文 |
| RBAC 扩展 | 新增 `DEPT_ADMIN` 角色：管理本部门资源，不跨部门 |

### 6.5 前端新页面 / 增强

| 页面 | 内容 |
|------|------|
| `BillingPage`（新建） | 部门消费仪表盘：预算进度环形图 + 7 天趋势折线 + 超额预警列表 |
| `InsightsPage` 增强 | 新增"ROI 报告"Tab：节省工时估算 + 下载 PDF |
| `AdminPage` 增强 | 部门管理：创建部门 → 绑定 AWS Account → 设置预算上限 |

### 6.6 基础设施

| 资源 | 变更 |
|------|------|
| IAM | 跨 Account AssumeRole（OrganizationAccountAccessRole），汇聚 Cost Explorer 数据 |
| EventBridge | 每月 1 日 00:00 UTC 触发 ROI 报告生成 |
| AWS Budgets | CDK 创建各部门 Budget（与 billing 模块 DB 记录双写） |
| S3 | 新增 `reports-bucket`：存储生成的 PDF 报告，预签名 URL 下载 |
| CDK | `BillingStack`（新建）：OrganizationRole + Budget + Reports Bucket |

### 6.7 验收标准

| 指标 | 目标 |
|------|------|
| 部门隔离覆盖 | 所有 Agent/工具/知识库 100% 有部门归属 |
| 预算告警时效 | 超额 80% 时 SNS 告警，P95 < 5 分钟 |
| ROI 报告自动化 | 每月 1 日自动生成所有部门报告，无需人工触发 |
| 跨 Account 成本聚合 | 支持 ≥5 个 AWS Account 汇聚 |

---

## 7. 里程碑总览

| 里程碑 | 时间窗口 | 核心交付 | 关键验收指标 |
|--------|:-------:|---------|-----------|
| **M13: 自动化评估** | 第 1-3 月 | Eval Pipeline + Bedrock Eval 集成 + 对比 Dashboard | ≥5 模板每日自动回归 |
| **M14: 生态扩展** | 第 4-6 月 | Builder MCP 对话式创建 + SSO/LDAP | 非技术自主创建率 ≥70% |
| **M15: 规模运营** | 第 7-10 月 | billing 模块 + 部门隔离 + ROI 报告 | 每部门独立成本视图 |
| **Phase 5 验收** | 第 10 月末 | 季度评审 + 全量质量门控 | 综合验收标准全部达标 |

### 新增模块概览

| 模块 | 类型 | 核心 AWS 能力 |
|------|:----:|------------|
| `evaluation` 扩展 | 扩展现有模块 | Bedrock Model Evaluation API |
| `builder` | 新建模块 | Claude Code MCP + AgentCore Gateway |
| `auth` 扩展（SSO + 部门） | 扩展现有模块 | SAML 2.0 + LDAP + JWT Claims |
| `billing` | 新建模块 | AWS Cost Explorer + Organizations |

### 变更积压预留

Phase 5 启动前执行一次**五维度季度评审**（代码审计 + 外部技术变化 + Phase 4 经验教训 + 路线图拆解 + 用户反馈），预估注入 12-15 项 S0-S4 变更，穿插执行。

---

## 8. 风险登记簿

| # | 风险 | 概率 | 严重度 | 缓解策略 |
|---|------|:----:|:------:|---------|
| R1 | Bedrock Model Evaluation API 仍处 GA 早期，接口可能变更 | 中 | 中 | 锁定 API 版本 + `BedrockEvalAdapter` 隔离；保留手动评分降级路径 |
| R2 | Claude Code MCP 调用延迟影响 Builder 体验 | 中 | 中 | 异步生成 + SSE 流式返回草稿；P95 < 5s 硬指标 |
| R3 | 企业 LDAP/SSO 配置复杂度超预期 | 中 | 高 | 先支持 SAML（标准化程度高）；LDAP 作为可选补充 |
| R4 | 多 AWS Account 权限配置复杂 | 中 | 中 | IAM 跨 Account AssumeRole 有成熟模式；提前与 AWS 账号管理团队对齐 |
| R5 | 部门隔离改造涉及全量实体 `department_id` 迁移 | 高 | 高 | 5C 启动前做 Alembic migration 预演；`department_id` 可为 NULL，渐进填充 |

---

## 9. 下一步

Phase 5 设计文档已批准。下一步：调用 `writing-plans` skill 创建 M13 详细实施计划。
