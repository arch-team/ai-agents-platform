# AI Agents Platform 技术设计文档

> **文档类型**: 技术入职文档 | **目标读者**: 新加入团队的中级工程师 | **最后更新**: 2026-03-02

---

## 1. 项目概述

AI Agents Platform 是一个基于 **Amazon Bedrock AgentCore** 的企业内部 AI Agents 平台。核心价值是让企业团队能够**创建、部署和管理 AI Agent**，实现从单 Agent 对话到多 Agent 协作（Agent Teams）的完整 Agent 生命周期管理。

### 1.1 当前状态

| 指标 | 数值 |
|------|------|
| **开发阶段** | Phase 6 — 平台智能化（M16 进行中） |
| **后端测试** | 2250+ 测试，覆盖率 88.29% |
| **前端测试** | 432+ 单元测试 |
| **基础设施测试** | 222+ 测试 |
| **测试总计** | 2904+ |
| **后端业务模块** | 11 个业务模块 + shared 共享内核 |
| **前端页面** | 13+ 页面，200+ 源文件 |
| **CI/CD 工作流** | 16 个 GitHub Actions Workflows |
| **CDK Stacks** | 13 个（含 dev + prod 双环境） |
| **Agent SDK** | claude-agent-sdk 0.1.35 + bedrock-agentcore 1.3.0 |

### 1.2 核心业务能力

- **Agent 管理**: 创建、配置、版本管理 Agent（状态机: draft -> active -> archived）
- **对话执行**: 单 Agent SSE 流式对话 + Agent Teams 多 Agent 协作
- **工具生态**: MCP Server / API / Function 三类工具注册与审批
- **知识库**: 文档上传 + RAG 检索（基于 Bedrock Knowledge Bases）
- **评估体系**: 测试集管理 + 批量评估 Pipeline + Bedrock Model Evaluation
- **对话式构建**: 通过 MCP 驱动的 Agent Builder 对话式创建 Agent
- **计费与配额**: 多租户部门计费 + 预算管理 + ROI 分析
- **审计合规**: 全操作审计日志 + 23 种领域事件订阅

---

## 2. 系统架构总览

### 2.1 系统架构图

```
                                    ┌──────────────────────┐
                                    │       用户浏览器       │
                                    └──────────┬───────────┘
                                               │ HTTPS
                                               v
                                    ┌──────────────────────┐
                                    │     CloudFront CDN    │
                                    │  (S3 Private + OAC)   │
                                    └──────────┬───────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │ 静态资源        │ API 请求        │
                              v                v                │
                    ┌──────────────┐  ┌──────────────────┐      │
                    │  S3 Bucket   │  │       ALB        │      │
                    │  (Frontend)  │  │  (HTTP:80/443)   │      │
                    └──────────────┘  └────────┬─────────┘      │
                                               │                │
                                               v                │
                                    ┌──────────────────────┐    │
                                    │   ECS Fargate Task    │    │
                                    │  ┌────────────────┐  │    │
                                    │  │  Platform API   │  │    │
                                    │  │  (FastAPI)      │  │    │
                                    │  └───┬──────┬─────┘  │    │
                                    └──────┼──────┼────────┘    │
                                           │      │              │
                          ┌────────────────┘      └──────────┐  │
                          v                                   v  │
               ┌──────────────────┐              ┌─────────────────────┐
               │  Aurora MySQL    │              │  AgentCore Runtime   │
               │  (Writer+Reader) │              │  (Agent 执行容器)     │
               └──────────────────┘              │  ┌───────────────┐  │
                                                 │  │Claude Agent SDK│  │
                                                 │  │  + CLI 子进程   │  │
                                                 │  └───────┬───────┘  │
                                                 └──────────┼──────────┘
                                                            │
                                           ┌────────────────┼──────────────┐
                                           v                v              v
                                ┌────────────────┐ ┌──────────────┐ ┌──────────┐
                                │ AgentCore      │ │   Bedrock    │ │    S3    │
                                │ Gateway (MCP)  │ │ (LLM 推理)   │ │(知识库)  │
                                │ ┌────────────┐ │ └──────────────┘ └──────────┘
                                │ │ MCP Server │ │
                                │ │ (工具集成)  │ │
                                │ └────────────┘ │
                                └────────────────┘
```

### 2.2 三个子项目

| 子项目 | 路径 | 技术栈 | 职责 |
|--------|------|--------|------|
| **后端** | `backend/` | Python + FastAPI | 业务 API、Agent 执行引擎、领域逻辑 |
| **前端** | `frontend/` | React + TypeScript + Vite | 用户界面、SSE 流式交互 |
| **基础设施** | `infra/` | AWS CDK + TypeScript | 云资源编排、环境管理、安全配置 |

---

## 3. 技术栈详解

### 3.1 后端

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 语言 | Python | 3.11+ | 推荐 3.12+ |
| Web 框架 | FastAPI | 0.110+ | 异步 ASGI |
| ORM | SQLAlchemy 2.0+ (async) | 2.0.25+ | asyncmy 驱动 |
| 数据验证 | Pydantic v2 | 2.6+ | 实体基类 + API Schema |
| 数据库 | MySQL 8.0+ / Aurora MySQL 3.x | - | 非 PostgreSQL |
| Agent SDK | claude-agent-sdk | 0.1.35+ | Agent 执行主路径 |
| AgentCore SDK | bedrock-agentcore | 1.3.0+ | Runtime 部署封装 |
| AWS SDK | boto3 | 1.36+ | AgentCore 控制面 + 降级路径 |
| 日志 | structlog | 24.x | 结构化 JSON 日志 |
| 认证 | python-jose + passlib | - | JWT + bcrypt |

### 3.2 前端

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | React | 19+ | 函数组件 + Hooks |
| 类型 | TypeScript | 5+ | strict 模式 |
| 构建 | Vite | 5+ | 开发 + 生产构建 |
| 样式 | TailwindCSS | 4+ | 原子化 CSS |
| 服务端状态 | TanStack Query (React Query) | 5+ | 缓存 + 失效 |
| 客户端状态 | Zustand | 4+ | 轻量全局状态 |
| 表单 | React Hook Form + Zod | 7+ / 3+ | 校验 + 类型推导 |

### 3.3 基础设施

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| IaC | AWS CDK | 2.130+ | 推荐 2.170+ |
| 语言 | TypeScript | 5+ | strict 模式 |
| 测试 | Jest + CDK Assertions | 29+ | Fine-grained + 快照 |
| 安全合规 | cdk-nag | 2.28+ | AWS Solutions 规则集 |

### 3.4 工具链

| 工具 | 用途 | 注意 |
|------|------|------|
| **uv** | Python 包管理 | **禁止** pip / poetry |
| **pnpm** | Node.js 包管理 | **禁止** npm / yarn |
| **Ruff** | Python Lint + Format | **禁止** flake8 / black / isort |
| **MyPy** | Python 类型检查 | strict 模式 |
| **pytest** | Python 测试 | 8.0+ |
| **Vitest** | 前端单元测试 | + Testing Library |
| **Playwright** | 前端 E2E 测试 | Page Object 模式 |
| **ESLint + Prettier** | 前端 Lint + Format | flat config (ESLint 9+) |

---

## 4. 后端架构设计

### 4.1 架构模式

后端采用 **DDD + Modular Monolith + Clean Architecture** 三者融合:

```
DDD (战术设计)          -> Entity, Value Object, Domain Event, Repository
Modular Monolith (模块化) -> 垂直切分业务模块，模块间松耦合
Clean Architecture (分层) -> 依赖倒置，核心业务与外部依赖隔离
```

**依赖方向**: API 层 -> Application 层 -> Domain 层 <- Infrastructure 层

**模块隔离原则**: 模块间不允许直接导入，必须通过 shared/ 共享内核或 EventBus 通信。

### 4.2 分层规则

每个业务模块内部严格遵循四层结构:

```
┌──────────────────────────────────────────────────┐
│                   API Layer                       │  <- 暴露 HTTP 端点
│       (endpoints, schemas, middleware)            │
├──────────────────────────────────────────────────┤
│               Application Layer                   │  <- 业务用例编排
│     (services, dto, interfaces, exceptions)       │
├──────────────────────────────────────────────────┤
│                 Domain Layer                      │  <- 核心业务逻辑
│  (entities, value_objects, services, repositories)│
├──────────────────────────────────────────────────┤
│             Infrastructure Layer                  │  <- 技术实现
│         (persistence, external adapters)          │
└──────────────────────────────────────────────────┘
```

**依赖合法性矩阵** (模块间导入规则):

| 从 ↓ 导入 -> | `shared/*` | `auth.api.deps` | 其他模块 Domain | 其他模块 Service | 其他模块 ORM Model |
|:-------------|:----------:|:---------------:|:--------------:|:---------------:|:-----------------:|
| **Domain** | OK | NO | NO | NO | NO |
| **Application** | OK | NO | NO | NO | NO |
| **Infrastructure** | OK | NO | NO | NO | FK only |
| **API** | OK | OK | NO | NO | NO |

**说明**:
- `shared/*` 是所有模块唯一允许的共享依赖
- `auth.api.dependencies` 的认证依赖（如 `get_current_user`）是唯一跨模块例外
- Infrastructure 层的 ORM Model 允许导入其他模块 ORM Model 定义外键关系

### 4.3 业务模块一览

| 模块 | 职责 | Phase | 端点数 |
|------|------|:-----:|:------:|
| **shared** | PydanticEntity 基类, IRepository, EventBus, DomainError, DB session, PydanticRepository | Phase 1 | - |
| **auth** | JWT + RBAC + SSO/SAML + LDAP + Rate Limiting (5 次失败锁 30 分钟) + Refresh Token | Phase 1 | 10+ |
| **agents** | Agent CRUD, 状态机 (draft -> active -> archived), AgentConfig, 工具绑定 | Phase 1 | 7 |
| **execution** | Agent 执行引擎, SSE 流式, IAgentRuntime 接口, Agent Teams (异步执行 + SSE 进度), Memory | Phase 1 | 12+ |
| **tool_catalog** | 企业工具注册, MCP Server / API / Function 三类工具, 5 状态审批流程 | Phase 2 | 10 |
| **knowledge** | 文档上传, RAG 检索 (Bedrock Knowledge Bases) | Phase 2 | 10 |
| **insights** | Token 归因, 使用趋势, CostExplorerAdapter (AWS 真实账单) | Phase 2 | 6 |
| **templates** | Agent 模板 CRUD, 状态机 (DRAFT -> PUBLISHED -> ARCHIVED), 7 分类, 10 预置模板 | Phase 2 | 8 |
| **audit** | 审计日志与合规, AuditLog append-only, EventBus 23 事件订阅 + HTTP 中间件 | Phase 4 | 5 |
| **evaluation** | 测试集管理 + 批量评估 + EvalPipeline + BedrockEvalAdapter + EventBridge 定时触发 | Phase 5 | 14 |
| **builder** | 对话式 Agent Builder (MCP 驱动), ClaudeBuilderAdapter, SSE 流式 | Phase 5 | 3 |
| **billing** | 多租户部门计费 + 预算管理 + ROI 报告 (CostExplorer) | Phase 5 | 10 |

### 4.4 关键设计模式

#### 4.4.1 IAgentRuntime 接口抽象 (Adapter Pattern)

Agent 执行层通过接口抽象支持多种运行时:

```
ExecutionService
  └── IAgentRuntime (接口)
        ├── ClaudeAgentAdapter (主路径)   <- claude-agent-sdk
        │     └── Claude Code CLI -> Bedrock Invoke API
        └── AgentCoreRuntimeAdapter (降级路径) <- boto3
              └── invoke_inline_agent -> AgentCore Runtime
```

- **ClaudeAgentAdapter**: 主执行路径，通过 claude-agent-sdk 调用 Claude Code CLI，支持完整 Agent Loop、Tool Use、MCP 集成
- **AgentCoreRuntimeAdapter**: 降级路径，通过 boto3 直接调用 AgentCore Runtime API

#### 4.4.2 EventBus 异步通信

模块间异步通信通过领域事件:

```python
# 定义事件
@dataclass
class AgentCreatedEvent(DomainEvent):
    agent_id: int
    owner_id: int

# 发布: await event_bus.publish_async(AgentCreatedEvent(...))
# 订阅: @event_handler(AgentCreatedEvent)
```

当前系统注册了 23 种领域事件，audit 模块通过 EventBus 订阅所有事件实现审计日志。

#### 4.4.3 Querier 跨模块同步查询模式

当模块 A 需要同步查询模块 B 的数据时（如 execution 查询 Agent 是否 ACTIVE），使用 Querier 模式:

| 角色 | 位置 | 职责 |
|------|------|------|
| **接口** | `shared/domain/interfaces/` | 方法签名 + 最小 DTO |
| **实现** | 提供方 `infrastructure/services/` | 实现接口 + 可选 TTLCache |
| **组装** | `presentation/api/providers.py` | Composition Root, 通过 DI 注入 |

当前 Querier 实例:

| 接口 | 消费方 | 提供方 |
|------|--------|--------|
| `IAgentQuerier` | execution | agents |
| `IToolQuerier` | execution | tool_catalog |
| `IKnowledgeQuerier` | execution | knowledge |

#### 4.4.4 PydanticEntity 基类

所有领域实体继承 `PydanticEntity`，自动获得 `id`, `created_at`, `updated_at` 字段。配合 `validate_assignment=True` 实现状态变更时的自动验证。

#### 4.4.5 PydanticRepository 基类

提供内置 CRUD 操作，通过 `_updatable_fields` 白名单控制可更新字段，避免意外覆盖关键字段。

### 4.5 目录结构

```
backend/
├── src/
│   ├── modules/                 # 12 个业务模块
│   │   ├── agents/
│   │   │   ├── api/             # FastAPI router + schemas
│   │   │   ├── application/     # Services + DTOs + interfaces
│   │   │   ├── domain/          # Entities + VOs + repos (接口)
│   │   │   └── infrastructure/  # ORM models + repo 实现
│   │   ├── auth/
│   │   ├── execution/
│   │   ├── tool_catalog/
│   │   ├── knowledge/
│   │   ├── insights/
│   │   ├── templates/
│   │   ├── audit/
│   │   ├── evaluation/
│   │   ├── builder/
│   │   └── billing/
│   ├── shared/                  # 跨模块共享内核
│   │   ├── api/                 # Exception handlers, 通用 schemas
│   │   ├── application/
│   │   ├── domain/              # PydanticEntity, IRepository, EventBus, DomainError
│   │   │   └── interfaces/      # IAgentQuerier, IToolQuerier 等跨模块接口
│   │   └── infrastructure/      # DB session (get_db), Settings, structlog 配置
│   └── presentation/api/        # FastAPI app 入口, 中间件, providers.py (DI 组装)
├── tests/                       # 镜像 src/ 结构
│   ├── conftest.py              # 全局 Fixture (双引擎: SQLite 默认 / --mysql)
│   ├── modules/
│   │   └── {module}/
│   │       ├── conftest.py      # 模块 Fixture 三件套
│   │       ├── unit/            # 单元测试 (Domain + Application)
│   │       └── integration/     # 集成测试 (Repository + API)
│   └── shared/
├── migrations/                  # Alembic 数据库迁移
└── pyproject.toml               # uv / ruff / mypy / pytest 统一配置
```

---

## 5. 前端架构设计

### 5.1 Feature-Sliced Design (FSD)

前端采用 **Feature-Sliced Design** 分层架构，核心规则是**只能向下依赖，不能向上或平级依赖**。

**FSD 分层依赖矩阵**:

| 从 ↓ 导入 -> | shared | entities | features | widgets | pages | app |
|:-------------|:------:|:--------:|:--------:|:-------:|:-----:|:---:|
| **app** | OK | OK | OK | OK | OK | - |
| **pages** | OK | OK | OK | OK | NO | NO |
| **widgets** | OK | OK | OK | NO | NO | NO |
| **features** | OK | OK | NO | NO | NO | NO |
| **entities** | OK | NO | NO | NO | NO | NO |
| **shared** | NO | NO | NO | NO | NO | NO |

各层级职责:

| 层级 | 职责 | 典型内容 |
|------|------|---------|
| **app** | 应用初始化 | App.tsx, routes, providers (QueryProvider, AuthProvider) |
| **pages** | 页面组装 | 组合 widgets + features，页面级布局 |
| **widgets** | 独立 UI 块 | Header, Sidebar, UserMenu |
| **features** | 业务功能 | LoginForm, AgentList, ChatInterface |
| **entities** | 数据模型 | User/Agent 类型定义 + 基础 UI (AgentCard) |
| **shared** | 共享工具 | Button, Input, API Client, hooks, utils |

### 5.2 状态管理策略

| 数据类型 | 方案 | 示例 |
|---------|------|------|
| 服务端数据 | TanStack Query (React Query) | Agent 列表、对话历史 |
| 全局 UI 状态 | Zustand | 主题、侧边栏状态 |
| 用户会话 | Zustand (内存，不持久化) | Token、登录状态 |
| 表单状态 | React Hook Form + Zod | 登录表单、Agent 配置表单 |
| 组件局部状态 | useState / useReducer | 下拉菜单开关 |

**关键安全约束**: Token 等敏感数据**禁止**存入 localStorage，仅保存在 Zustand 内存中。

### 5.3 页面模块 (15 pages)

| 页面 | 路由 | 功能 |
|------|------|------|
| login | `/login` | 登录 |
| register | `/register` | 注册 |
| dashboard | `/` | 仪表盘概览 |
| agents | `/agents` | Agent 列表与管理 |
| chat | `/chat/:id` | 单 Agent 对话 |
| team-executions | `/team-executions` | Agent Teams 任务管理 |
| tools | `/tools` | 工具目录管理 |
| knowledge | `/knowledge` | 知识库管理 |
| templates | `/templates` | 模板管理 |
| insights | `/insights` | 使用分析 |
| evaluation | `/evaluation` | 评估管理 |
| builder | `/builder` | Agent Builder |
| billing | `/billing` | 计费管理 |
| admin | `/admin` | 管理员面板 |
| not-found | `*` | 404 页面 |

### 5.4 Features 模块 (12 features)

每个 feature 遵循标准 slice 结构: `api/` (queries + mutations) + `model/` (store + types) + `ui/` (组件) + `lib/` (工具函数)

auth, agents, execution, team-executions, tool-catalog, knowledge, templates, insights, evaluation, builder, billing, dashboard

### 5.5 SSE 流式通信三层架构

Agent 对话和 Teams 执行都使用 SSE (Server-Sent Events) 流式通信:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Feature Stream Hook                                │
│  features/*/api/stream.ts                                    │
│  useRef<AbortController> 生命周期 + Zustand 流式状态管理       │
│  finally 块 invalidateQueries 刷新缓存                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Feature 适配器                                      │
│  features/*/lib/sse.ts                                       │
│  指定 chunk 类型 + HTTP 方法 (POST/GET), yield* 委托 shared    │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Shared 解析器                                       │
│  shared/lib/parseSSEStream.ts                                │
│  泛型 async function* 生成器, buffer/line splitting/错误区分   │
└─────────────────────────────────────────────────────────────┘
```

关键约定:
- SSE 不使用 React Query mutation（流式状态由 Zustand 管理）
- Token 由调用方传入（避免跨 feature 依赖 auth store）
- 组件卸载时通过 `AbortController.abort()` 取消连接

---

## 6. 基础设施设计

### 6.1 CDK Stack 体系

Stack 部署依赖关系（从左到右依次部署）:

```
NetworkStack -> SecurityStack -> DatabaseStack -> ComputeStack -> AgentCoreStack
                                                                      |
                                                          FrontendStack (独立)
                                                          BillingStack  (独立)
                                                          MonitoringStack (最后)
```

| Stack | 命名模式 | 关键资源 |
|-------|---------|---------|
| **NetworkStack** | `ai-agents-plat-network-{env}` | VPC (3 AZ), Public/Private/Isolated Subnets, NAT Gateway, S3 VPC Endpoint |
| **SecurityStack** | `ai-agents-plat-security-{env}` | Security Groups (API/DB), KMS Key, JWT Secret (Secrets Manager), VPC Endpoints |
| **DatabaseStack** | `ai-agents-plat-database-{env}` | Aurora MySQL 3.10.0, S3 Knowledge Bucket, Secrets Manager (DB 密码) |
| **ComputeStack** | `ai-agents-plat-compute-{env}` | ECS Fargate (Task Definition + Service), ALB (HTTP:80), Auto Scaling |
| **AgentCoreStack** | `ai-agents-plat-agentcore-{env}` | ECR (Agent 镜像), AgentCore Runtime (2 AZ), AgentCore Gateway (MCP), Cognito |
| **FrontendStack** | `ai-agents-plat-frontend-{env}` | S3 Private Bucket + CloudFront OAC (Origin Access Control) |
| **BillingStack** | `ai-agents-plat-billing-{env}` | AWS Budgets 月度告警 (Dev $100, Prod $1000), CloudWatch 成本 Widget |
| **MonitoringStack** | `ai-agents-plat-monitoring-{env}` | CloudWatch Alarms + Dashboard, SNS 告警 |

### 6.2 环境策略

| 维度 | Dev 环境 | Prod 环境 |
|------|---------|----------|
| **用途** | 开发 + 验证 | 生产 |
| **ECS** | 256 CPU / 512 MiB / 1 任务 | 512 CPU / 1024 MiB / 2 任务 |
| **Aurora** | db.t3.medium, 单实例 | db.r6g.large, Writer + Reader (多 AZ) |
| **NAT** | 1 个 | 每 AZ 一个 |
| **RemovalPolicy** | DESTROY | RETAIN (S3) / SNAPSHOT (RDS) |
| **日志保留** | 1 周 | 1 年 |
| **Staging** | 无 (v1.4 简化，当前仅 dev + prod) | - |

### 6.3 CI/CD Pipeline (16 个工作流)

**PR 触发**:

| 工作流 | 触发条件 | 内容 |
|--------|---------|------|
| `backend-ci.yml` | PR 涉及 backend/ | 运行后端 CI |
| `backend-quality.yml` | 由 backend-ci 调用 | ruff + mypy + pytest |
| `frontend-ci.yml` | PR 涉及 frontend/ | 运行前端 CI |
| `frontend-quality.yml` | 由 frontend-ci 调用 | lint + typecheck + test + build |
| `workflow-lint.yml` | PR 涉及 .github/ | 工作流语法检查 |

**部署**:

| 工作流 | 触发条件 | 内容 |
|--------|---------|------|
| `backend-deploy.yml` | main 分支 + backend/ 变更 | dev 自动部署, prod 手动审批 |
| `frontend-deploy.yml` | main 分支 + frontend/ 变更 | S3 + CloudFront 部署 |
| `cdk-deploy.yml` | main 分支 + infra/ 变更 | CDK Stack 部署 |

**运维**:

| 工作流 | 频率 | 内容 |
|--------|------|------|
| `security-scan.yml` | 每周 | 依赖漏洞扫描 |
| `performance-test.yml` | 每周 | 性能基线测试 |
| `backup-verify.yml` | 每月 | 备份验证 |
| `drift-detection.yml` | 每周 | CloudFormation Drift 检测 |

**辅助**:

| 工作流 | 用途 |
|--------|------|
| `release.yml` | 手动触发, git-cliff 生成 changelog |
| `agent-image.yml` | Agent 镜像推送到 ECR |
| `deploy-notify.yml` | 部署失败自动创建 GitHub Issue |
| `labeler.yml` | PR 自动打标签 |

---

## 7. Agent 执行架构

### 7.1 双路径架构 (ADR-006)

```
ExecutionService
  └── IAgentRuntime (接口)
        │
        ├── ClaudeAgentAdapter (主路径)
        │     └── claude-agent-sdk
        │           └── claude_agent_sdk.query()
        │                 └── fork Claude Code CLI 子进程 (Node.js SEA)
        │                       ├── stdio pipe <-> Python SDK 进程
        │                       ├── Bedrock Invoke API (HTTPS)
        │                       └── MCP Server 连接
        │
        └── AgentCoreRuntimeAdapter (降级路径)
              └── boto3
                    └── invoke_inline_agent
                          └── AgentCore Runtime 托管容器
```

**两种运行时模式** (ADR-014):

| 维度 | in_process 模式 | agentcore_runtime 模式 |
|------|----------------|----------------------|
| 执行位置 | ECS 容器内 (CLI 子进程) | AgentCore 独立托管容器 |
| 进程隔离 | 无 — CLI 与 API 共享资源 | 完全隔离 |
| 启动延迟 | ~2s (CLI fork) | ~5-10s (容器冷启动) |
| 适用场景 | 开发调试、轻量 Agent | 生产负载、长时间执行、Teams |
| CDK Context | `--context agentRuntimeMode=in_process` | 默认值 |

### 7.2 Agent Teams (ADR-008)

Agent Teams 替代了原规划的 DAG 引擎（`orchestration` 模块已取消），在 `execution` 模块内扩展实现多 Agent 协作:

- **启用方式**: 环境变量 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- **内置工具**: TeamCreate, SendMessage, TaskCreate, TaskUpdate, TaskList
- **编排模式**: Agent 自主编排（LLM 决定团队结构和分工），非预定义 DAG
- **领域模型**: `TeamExecution` 实体，状态机: PENDING -> RUNNING -> COMPLETED / FAILED / CANCELLED
- **异步执行**: `asyncio.Task` 后台执行 + `asyncio.Semaphore(3)` 并发控制
- **API**: 5 个端点 (POST 创建, GET 列表/详情, GET /stream SSE, POST /cancel)

### 7.3 MCP 集成三种模式

| 模式 | 说明 | 使用场景 |
|------|------|---------|
| **AgentCore Gateway SSE** | 远程 MCP Server，通过 AgentCore Gateway 统一入口 | 企业工具目录中注册的工具 |
| **SDK 进程内 MCP Server** | Python 进程内运行的 MCP Server | 平台内置工具 (platform-tools) |
| **Memory MCP Server** | AgentCore Memory 通过 MCP 桥接到 Agent SDK | Agent 记忆读写 (ADR-014) |

---

## 8. 安全体系

| 安全层面 | 实现方案 |
|---------|---------|
| **认证** | JWT (python-jose) + RBAC (admin/user 角色) + SSO/SAML 2.0 (python3-saml3) + LDAP (ldap3) |
| **密码安全** | bcrypt (rounds=12) + Rate Limiting (5 次失败 -> 30 分钟锁定) |
| **API 安全** | OAuth2 Bearer Token + Refresh Token 轮换 |
| **数据加密** | Aurora 静态加密 (KMS) + S3 SSE + HTTPS 全链路 TLS |
| **密钥管理** | AWS Secrets Manager (DB 密码, JWT 密钥) — 禁止硬编码 |
| **审计** | audit 模块全操作审计日志 (EventBus 23 事件 + HTTP 中间件) |
| **CDK 合规** | cdk-nag AwsSolutionsChecks 自动安全检查 |
| **网络分层** | VPC 三层子网: PUBLIC (ALB) / PRIVATE_WITH_EGRESS (ECS) / PRIVATE_ISOLATED (Aurora) |
| **权限控制** | IAM 最小权限 — 使用 CDK Grant 方法，禁止 `actions: ['*']` |
| **输入验证** | Pydantic v2 (后端) + Zod (前端) — 参数化查询，禁止 SQL 拼接 |
| **日志脱敏** | 密码完全隐藏, Token 保留前 4 位, 邮箱部分隐藏 |
| **前端安全** | 禁止 `dangerouslySetInnerHTML` (除非 DOMPurify), 禁止 localStorage 存 Token |

---

## 9. 可观测性

### 9.1 三大支柱

| 支柱 | 工具 | 配置 |
|------|------|------|
| **Logs** | structlog -> CloudWatch Logs | Dev: 彩色控制台, Prod: JSON 格式 |
| **Metrics** | OpenTelemetry -> CloudWatch Metrics | `http_requests_total`, `agent_execution_duration_seconds` 等 |
| **Traces** | OpenTelemetry -> AWS X-Ray | Span: `{method} {path}`, `agent.execute` 等 |

### 9.2 Correlation ID

通过 `X-Correlation-ID` HTTP Header 贯穿整个请求链路:

```
HTTP 请求 (X-Correlation-ID Header)
  -> structlog contextvars 自动注入
  -> Domain Event 属性传递
  -> 异步任务参数携带
```

### 9.3 Health Check

| 端点 | 用途 | 返回 |
|------|------|------|
| `GET /health` | 存活检查 (Liveness) | `{"status": "ok"}` |
| `GET /health/ready` | 就绪检查 (Readiness) | `{"status": "ok", "checks": {...}}` |

就绪检查包含数据库 `SELECT 1` (3s 超时) 等依赖检查。失败返回 503 + `"degraded"` 状态。

### 9.4 CloudWatch Dashboard

MonitoringStack 配置了自定义 CloudWatch Dashboard，监控:
- Aurora 连接数、查询延迟
- ECS CPU/Memory 利用率
- ALB 请求量、5xx 错误率
- Agent 执行耗时和 Token 消耗

---

## 10. 数据模型概要

核心实体及其关系:

```
┌──────────┐       1:N       ┌──────────┐       1:N       ┌──────────────┐
│   User   │ ──────────────> │   Agent  │ ──────────────> │ Conversation │
│  (auth)  │                 │ (agents) │                 │ (execution)  │
└──────────┘                 └────┬─────┘                 └──────┬───────┘
     │                            │                              │
     │                            │ N:N (AgentTool, M16)         │ 1:N
     │                            v                              v
     │                     ┌──────────┐                   ┌──────────┐
     │                     │   Tool   │                   │  Message │
     │                     │(tool_cat)│                   │(execution│
     │                     └──────────┘                   └──────────┘
     │
     │                     ┌──────────────┐
     │  1:N                │KnowledgeBase │
     │  (Department)       │ (knowledge)  │
     v                     └──────────────┘
┌──────────────┐                 ^
│  Department  │                 │ N:N
│  (billing)   │           ┌────┴─────┐
└──────────────┘           │   Agent  │
                           └──────────┘

┌──────────────┐  instantiate  ┌──────────┐
│   Template   │ ────────────> │   Agent  │
│ (templates)  │               │          │
└──────────────┘               └──────────┘

┌──────────────┐  subscribe    ┌───────────────────┐
│   AuditLog   │ <──────────── │ All Domain Events │
│   (audit)    │  (EventBus)   │  (23 种事件)       │
└──────────────┘               └───────────────────┘

┌──────────────────────┐
│   TeamExecution      │  Agent Teams 异步多 Agent 协作
│   (execution)        │
│   + TeamExecutionLog │
└──────────────────────┘

┌──────────────┐              ┌────────────────┐
│   TestSuite  │ ──────────>  │ EvaluationRun  │
│  + TestCase  │  批量评估     │ + EvalResult   │
│ (evaluation) │              │ (evaluation)   │
└──────────────┘              └────────────────┘
```

**关键关系说明**:
- User (auth) 1:N Agent (agents): 用户创建和拥有 Agent
- Agent 1:N Conversation 1:N Message: 对话执行链
- Agent N:N Tool (M16 工具绑定): 通过 AgentTool 关联表
- Agent N:N KnowledgeBase: Agent 可关联多个知识库
- Template -> instantiates -> Agent: 模板实例化为 Agent
- Agent -> Memory (execution, via MCP): Agent 记忆通过 MCP Memory Server 读写
- Department (billing) 1:N User: 部门包含多个用户，用于计费归属
- AuditLog (audit) 订阅所有领域事件: 全操作审计追踪

---

## 11. 关键 ADR 索引

| ADR | 标题 | 状态 | 核心决策 |
|:---:|------|:----:|---------|
| 001 | 架构模式选型 | 已采纳 | DDD + Modular Monolith + Clean Architecture |
| 002 | 技术栈选型 | 已采纳 | Python + FastAPI + SQLAlchemy + Pydantic |
| 003 | AgentCore 基础设施 | 已采纳 | AgentCore 为核心部署平台 |
| 005 | 数据库引擎选型 | 已采纳 | Aurora MySQL 3.x (非 PostgreSQL) |
| 006 | Agent 框架选型 | 已采纳 | Claude Agent SDK 为唯一框架 + IAgentRuntime 接口抽象 |
| 007 | Phase 3 路线图调整 | 已采纳 | 路线图从 24 月缩至 18 月, marketplace 模块移除 |
| 008 | Agent Teams 替代 DAG | 已采纳 | Agent Teams 替代 orchestration 模块, 在 execution 内扩展 |
| 009 | Phase 3 季度评审 | 已采纳 | 前端优先级提升, evaluation 精简 |
| 010 | Opus 4.6 模型评估 | 已采纳 | 支持 Opus 4.6 用于高端任务 |
| 011 | A2A 协议评估 | 已采纳 | 观望态度, Agent Teams 已满足当前需求 |
| 012 | 蓝绿部署评估 | 已采纳 | 当前 ECS 滚动更新, 蓝绿部署推迟至需要时 |
| 013 | Strands SDK 评估 | 已采纳 | 不迁移到 Strands, 保持观察 |
| 014 | Agent Runtime MCP Memory | 已采纳 | Memory MCP 架构设计, 双模式运行时 |

ADR 文档位于 `docs/adr/` 目录，编号与上表对应。

---

## 12. 本地开发快速上手

### 12.1 前置条件

| 工具 | 版本要求 | 安装方式 |
|------|---------|---------|
| Python | 3.11+ | `pyenv install 3.12` 或系统安装 |
| Node.js | 22 LTS | `nvm install 22` 或官网下载 |
| uv | 最新 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| pnpm | 9.x | `npm install -g pnpm` |
| Docker | 最新 | Docker Desktop |

### 12.2 后端启动

```bash
# 1. 进入后端目录并安装依赖
cd backend
uv sync

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写必要配置 (数据库连接、JWT Secret 等)

# 3. 启动本地 MySQL
docker run -d \
  --name mysql-dev \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=changeme \
  -e MYSQL_DATABASE=ai_agents_platform \
  mysql:8.0

# 4. 运行数据库迁移 (如有)
uv run alembic upgrade head

# 5. 启动开发服务
uv run uvicorn src.presentation.api.main:app --reload --port 8000

# API 文档访问: http://localhost:8000/docs
```

### 12.3 前端启动

```bash
# 1. 进入前端目录并安装依赖
cd frontend
pnpm install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 设置 VITE_API_BASE_URL=http://localhost:8000

# 3. 启动开发服务 (Vite)
pnpm run start

# 访问: http://localhost:5173
```

### 12.4 基础设施 (可选)

```bash
# 1. 进入基础设施目录
cd infra
pnpm install

# 2. 合成 CloudFormation 模板 (验证代码正确性)
pnpm cdk synth

# 3. 部署到 AWS (需要 AWS 凭证)
pnpm cdk deploy --all --context env=dev
```

### 12.5 质量检查命令

**后端**:
```bash
cd backend

# Lint 检查
uv run ruff check src/

# 类型检查
uv run mypy src/

# 运行测试 (默认 SQLite 内存数据库)
uv run pytest

# 测试 + 覆盖率
uv run pytest --cov=src --cov-report=term-missing

# 一键全量检查 (PR 提交前必须通过)
uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/ && uv run pytest --cov=src --cov-fail-under=85
```

**前端**:
```bash
cd frontend

# Lint + 类型 + 测试
pnpm lint && pnpm typecheck && pnpm test

# 一键全量检查
pnpm lint && pnpm format:check && pnpm typecheck && pnpm test:coverage
```

**基础设施**:
```bash
cd infra

# Lint + 类型 + 测试 + CDK 合成
pnpm lint && pnpm typecheck && pnpm test && pnpm cdk synth
```

---

## 13. 规范文档导航

### 13.1 后端规范

| 主题 | 文档路径 | 说明 |
|------|---------|------|
| 后端入口 | `backend/.claude/CLAUDE.md` | 技术栈、开发命令、覆盖率要求 |
| 架构规范 | `backend/.claude/rules/architecture.md` | 四层规则、模块隔离、Querier 模式 |
| 测试规范 | `backend/.claude/rules/testing.md` | TDD 工作流、Fixture 三件套、双引擎策略 |
| 代码风格 | `backend/.claude/rules/code-style.md` | 类型提示、命名、Docstring、异步规范 |
| 安全规范 | `backend/.claude/rules/security.md` | OWASP 速查表、安全检测命令 |
| API 设计 | `backend/.claude/rules/api-design.md` | RESTful 路由、状态码、分页、错误格式 |
| SDK 优先 | `backend/.claude/rules/sdk-first.md` | SDK 决策流程、异常映射 |
| 日志规范 | `backend/.claude/rules/logging.md` | structlog、Correlation ID、脱敏规则 |
| 可观测性 | `backend/.claude/rules/observability.md` | Metrics 命名、Tracing、Health Check |
| PR 检查清单 | `backend/.claude/rules/checklist.md` | 架构/代码/安全/测试/API 检查项 |

### 13.2 前端规范

| 主题 | 文档路径 | 说明 |
|------|---------|------|
| 前端入口 | `frontend/.claude/CLAUDE.md` | 技术栈、开发命令 |
| 架构规范 | `frontend/.claude/rules/architecture.md` | FSD 分层、SSE 三层架构 |
| 组件设计 | `frontend/.claude/rules/component-design.md` | 展示/容器/复合组件模式 |
| 状态管理 | `frontend/.claude/rules/state-management.md` | Query / Zustand / Form 策略 |
| 代码风格 | `frontend/.claude/rules/code-style.md` | 命名、TypeScript、导入排序 |
| 测试规范 | `frontend/.claude/rules/testing.md` | Vitest + Testing Library + MSW |
| 安全规范 | `frontend/.claude/rules/security.md` | XSS 防护、Token 存储 |
| 无障碍 | `frontend/.claude/rules/accessibility.md` | WCAG 2.1 AA、ARIA、键盘导航 |
| 性能优化 | `frontend/.claude/rules/performance.md` | 代码分割、Memoization、虚拟列表 |

### 13.3 基础设施规范

| 主题 | 文档路径 | 说明 |
|------|---------|------|
| 基础设施入口 | `infra/.claude/CLAUDE.md` | CDK 命令、注意事项 |
| 架构规范 | `infra/.claude/rules/architecture.md` | Stack 设计、Construct 分层、跨 Stack 通信 |
| Construct 设计 | `infra/.claude/rules/construct-design.md` | Props 接口、安全默认配置、JSDoc |
| 安全规范 | `infra/.claude/rules/security.md` | IAM 最小权限、CDK Nag、数据加密 |
| 测试规范 | `infra/.claude/rules/testing.md` | Fine-grained + 快照 + CDK Nag 合规 |
| 部署规范 | `infra/.claude/rules/deployment.md` | 环境矩阵、CI/CD、回滚策略 |
| 成本优化 | `infra/.claude/rules/cost-optimization.md` | 资源选型、Dev 定时缩减 |

### 13.4 项目级文档

| 主题 | 文档路径 | 说明 |
|------|---------|------|
| 项目进度 | `docs/progress.md` | 每次会话必读，任务追踪 |
| 路线图 | `docs/strategy/roadmap.md` | 6 阶段规划 |
| 改进计划 | `docs/strategy/improvement-plan.md` | 变更积压来源 |
| ADR 索引 | `docs/adr/README.md` | 架构决策记录列表 |
| 贡献指南 | `docs/CONTRIB.md` | 环境配置、脚本、CI/CD |
| 运维手册 | `docs/RUNBOOK.md` | 部署、监控、故障排查 |
| Git 工作流 | `CONTRIBUTING.md` | GitHub Flow、分支命名 |
| 通用规则 | `.claude/rules/common.md` | Git 提交规范、Monorepo 结构 |
