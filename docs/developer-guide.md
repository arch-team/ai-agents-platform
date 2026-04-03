# AI Agents Platform — 开发者完全指南

> **文档定位**: 面向平台代码贡献者和 API 消费者的一站式开发者文档
>
> **目标读者**: 后端/前端/基础设施工程师、API 集成开发者
>
> **最后更新**: 2026-03-31

---

## 目录

1. [项目概述与核心概念](#1-项目概述与核心概念)
2. [系统架构全景](#2-系统架构全景)
3. [后端模块开发指南](#3-后端模块开发指南)
4. [前端模块开发指南](#4-前端模块开发指南)
5. [基础设施与 CDK 开发指南](#5-基础设施与-cdk-开发指南)
6. [API 参考文档](#6-api-参考文档)
7. [测试策略深度指南](#7-测试策略深度指南)
8. [部署与环境管理](#8-部署与环境管理)
9. [AgentCore 集成架构解析](#9-agentcore-集成架构解析)
10. [常见问题与故障排查](#10-常见问题与故障排查)

---

## 1. 项目概述与核心概念

### 1.1 平台定位

AI Agents Platform 是基于 **Amazon Bedrock AgentCore** 的企业内部 AI Agents 平台。核心使命是让企业团队能够**创建、部署和管理 AI Agent**，覆盖从单 Agent 对话到多 Agent 协作（Agent Teams）的完整 Agent 生命周期。

**核心价值**:

| 价值 | 说明 |
|------|------|
| **统一管理** | 集中管理企业内所有 AI Agent 的创建、配置、部署和版本迭代 |
| **编排协作** | 基于 Agent Teams 的多 Agent 自主协作，实现复杂业务场景自动化 |
| **可观测性** | 完整的执行监控、性能追踪、成本核算和质量评估体系 |
| **安全合规** | RBAC 权限控制 + SSO/LDAP + 全操作审计日志 + 部门资源隔离 |
| **扩展性** | MCP 工具集成 + 多模型支持 + 知识库 RAG 检索 |

### 1.2 当前状态

| 指标 | 数值 |
|------|------|
| 开发阶段 | Phase 6 — 平台智能化（M16 进行中） |
| 后端业务模块 | 11 个 + shared 共享内核 |
| 前端页面 | 15 个页面，200+ 源文件 |
| 测试总计 | 2904+（后端 2250+ / 前端 432+ / CDK 222+） |
| 后端覆盖率 | 88.29% |
| CI/CD 工作流 | 16 个 GitHub Actions Workflows |
| CDK Stacks | 8 种 Stack（含 dev + prod 双环境） |

### 1.3 技术栈总览

| 子项目 | 架构模式 | 技术栈 |
|--------|---------|--------|
| **后端** | DDD + Modular Monolith + Clean Architecture | Python 3.12 / FastAPI / SQLAlchemy 2.0 (async) / Pydantic v2 / MySQL 8.0 |
| **前端** | Feature-Sliced Design (FSD) | React 19 / TypeScript 5 / Vite 5 / TailwindCSS 4 / TanStack Query 5 / Zustand 4 |
| **基础设施** | Construct 分层 (L1→L2→L3) | AWS CDK / TypeScript / Jest / cdk-nag |
| **Agent SDK** | 双路径架构 (ADR-006) | claude-agent-sdk 0.1.35 + bedrock-agentcore 1.3.0 + boto3 1.36+ |

### 1.4 架构模式说明

**后端三合一架构**:

```
DDD (战术设计)          → Entity, Value Object, Domain Event, Repository
Modular Monolith (模块化) → 垂直切分业务模块，模块间松耦合
Clean Architecture (分层) → 依赖倒置，核心业务与外部依赖隔离
```

**前端 FSD 分层**: `app → pages → widgets → features → entities → shared`（只能向下依赖，不能向上或平级依赖）

**CDK Construct 分层**: `L1 (CfnResource)` → `L2 (CDK Construct)` → `L3 (自定义高级 Construct)`

### 1.5 Monorepo 结构

```
ai-agents-platform/
├── backend/            # 后端服务 (Python + FastAPI)
│   ├── src/modules/    # 11 个业务模块 + shared 共享内核
│   ├── src/shared/     # 共享内核（PydanticEntity, IRepository, EventBus）
│   ├── tests/          # 测试（镜像 src/ 结构）
│   └── migrations/     # Alembic 数据库迁移
├── frontend/           # 前端应用 (React + TypeScript + Vite)
│   └── src/            # app / pages / widgets / features / entities / shared
├── infra/              # 基础设施 (AWS CDK + TypeScript)
│   └── lib/stacks/     # 8 种 CDK Stack
├── docs/               # 项目文档
│   ├── adr/            # 架构决策记录 (14 个 ADR)
│   ├── strategy/       # 战略规划 (roadmap, improvement-plan)
│   ├── onboarding/     # 入职指南
│   └── user-guide/     # 用户使用指南
└── scripts/            # 工具脚本 (loadtest, DR 验证)
```

### 1.6 环境准备

#### 系统要求

| 工具 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Python | 3.11 | 3.12+ | 后端运行时 |
| Node.js | 18.0 | 22 LTS | 前端 + CDK + Claude Agent SDK 依赖 |
| uv | - | 最新 | 后端 Python 包管理（**禁止** pip/poetry） |
| pnpm | 8.0 | 10.x | 前端 + CDK 包管理（**禁止** npm/yarn） |
| Docker | - | 最新 | 本地数据库 |
| AWS CLI | 2.x | 最新 | CDK 部署 |

#### 快速启动

```bash
# 克隆仓库
git clone <repo-url> && cd ai-agents-platform

# 后端
cd backend && uv sync && cd ..

# 前端
cd frontend && pnpm install && cd ..

# 基础设施
cd infra && pnpm install && cd ..

# 配置环境变量
cp backend/.env.example backend/.env    # 本地开发直接使用默认值即可

# 启动本地 MySQL
docker run -d --name mysql-dev -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=changeme \
  -e MYSQL_DATABASE=ai_agents_platform mysql:8.0

# 运行数据库迁移
cd backend && uv run alembic upgrade head && cd ..

# 启动后端开发服务（首次启动自动创建默认管理员账户）
cd backend && uv run uvicorn src.presentation.api.main:app --reload --port 8000

# 启动前端开发服务
cd frontend && pnpm dev
```

#### 验证安装

```bash
python --version && node --version && uv --version   # 版本检查
cd backend && uv run python -c "import fastapi; print(fastapi.__version__)"
cd frontend && pnpm typecheck
cd infra && pnpm exec cdk --version
```

### 1.7 工具链与环境配置

#### 强制工具链

| 类别 | 工具 | 说明 | 禁止替代 |
|------|------|------|---------|
| Python 包管理 | **uv** | 所有依赖安装、虚拟环境管理 | pip, poetry, conda |
| Node.js 包管理 | **pnpm** | 前端和 CDK 依赖管理 | npm, yarn |
| Python Lint + Format | **Ruff** | 代码检查 + 格式化一体 | flake8, black, isort |
| Python 类型检查 | **MyPy** | strict 模式 | pyright |
| 前端 Lint | **ESLint 9+** | flat config 模式 | - |
| 前端 Format | **Prettier** | 代码格式化 | - |

#### 关键环境变量 (`backend/.env.example`)

| 变量 | 默认值 | 说明 |
|------|-------|------|
| `DATABASE_HOST` | `localhost` | 数据库主机 |
| `DATABASE_PORT` | `3306` | 数据库端口 |
| `DATABASE_NAME` | `ai_agents_platform` | 数据库名 |
| `DATABASE_USER` / `DATABASE_PASSWORD` | `root` / `changeme` | 数据库凭证（部署环境由 Secrets Manager 注入） |
| `JWT_SECRET_KEY` | `changeme-use-a-strong-secret-key` | JWT 签名密钥 |
| `AWS_REGION` | `us-east-1` | AWS 区域 |
| `DEFAULT_ADMIN_EMAIL` | `admin@company.com` | 默认管理员（启动时自动创建，幂等） |
| `LOG_LEVEL` | `DEBUG` | 日志级别 |

前端仅需 `VITE_API_BASE_URL=http://localhost:8000`。

### 1.8 术语表

| 术语 | 定义 |
|------|------|
| **Agent** | 具有特定配置（模型、Prompt、工具）的 AI 智能体，状态机: DRAFT → ACTIVE → ARCHIVED |
| **Agent Teams** | 基于 Claude Agent SDK 的多 Agent 自主协作机制，Agent 自行组建团队、分配任务（替代传统 DAG 引擎） |
| **AgentCore** | Amazon Bedrock AgentCore — AWS 提供的 Agent 运行时托管和治理平台 |
| **AgentCore Runtime** | AgentCore 的独立容器执行环境，Agent 在其中运行（vs. 进程内执行） |
| **AgentCore Gateway** | AgentCore 的 MCP 统一入口，管理企业工具的访问和调用 |
| **MCP** | Model Context Protocol — Anthropic 定义的 AI Agent 工具调用标准协议 |
| **SSE** | Server-Sent Events — Agent 对话和 Teams 执行使用的流式通信协议 |
| **RBAC** | Role-Based Access Control — 基于角色的权限控制（admin/user 两种角色） |
| **DDD** | Domain-Driven Design — 领域驱动设计，业务逻辑组织方式 |
| **FSD** | Feature-Sliced Design — 前端功能切片架构 |
| **EventBus** | 领域事件总线 — 模块间异步通信机制 |
| **Querier** | 跨模块同步查询模式 — 模块间数据查询的接口抽象 |
| **PydanticEntity** | 项目自定义的领域实体基类，自动提供 id/created_at/updated_at |
| **PydanticRepository** | 项目自定义的仓储基类，内置 CRUD 操作 |

### 1.9 关键 ADR 索引

| ADR | 标题 | 核心决策 |
|:---:|------|---------|
| 001 | 架构模式选型 | DDD + Modular Monolith + Clean Architecture |
| 002 | 技术栈选型 | Python + FastAPI + SQLAlchemy + Pydantic |
| 005 | 数据库引擎选型 | Aurora MySQL 3.x（非 PostgreSQL） |
| 006 | Agent 框架选型 | Claude Agent SDK 为唯一框架 + IAgentRuntime 接口抽象 |
| 008 | Agent Teams 替代 DAG | Agent Teams 替代 orchestration 模块 |
| 014 | Agent Runtime MCP Memory | Memory MCP 架构 + 双模式运行时 (in_process / agentcore_runtime) |

完整 ADR 列表见 `docs/adr/` 目录（共 14 个）。

### 1.10 相关文档导航

| 文档 | 说明 | 何时阅读 |
|------|------|---------|
| [开发贡献指南](CONTRIB.md) | 脚本命令速查、CI/CD 工作流、Git 规范 | 日常开发参考 |
| [运维手册](RUNBOOK.md) | 部署流程、监控告警、故障排查、回滚 | 部署和运维时 |
| [技术设计文档](technical-design.md) | 完整技术架构细节 | 深入了解架构 |
| [路线图](strategy/roadmap.md) | 六阶段迭代规划和验收标准 | 了解产品演进 |
| [产品架构蓝图](strategy/product-architecture.md) | 六大核心能力模块映射 | 理解能力全景 |
| 后端规范 (`backend/.claude/rules/`) | 架构、测试、代码风格、安全等详细规范 | 编写后端代码时 |
| 前端规范 (`frontend/.claude/rules/`) | FSD 架构、组件设计、状态管理规范 | 编写前端代码时 |
| CDK 规范 (`infra/.claude/rules/`) | Stack 设计、Construct 规范 | 修改基础设施时 |

---

## 2. 系统架构全景

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

**数据流向说明**:
- **静态资源**: 用户浏览器 → CloudFront → S3（前端 SPA）
- **API 请求**: 用户浏览器 → CloudFront → ALB → ECS Fargate（Platform API）
- **Agent 执行**: Platform API → AgentCore Runtime → Bedrock LLM + MCP 工具
- **数据持久化**: Platform API → Aurora MySQL（业务数据）+ S3（知识库文档）

### 2.2 请求生命周期

一个典型的 API 请求从进入到返回经历以下环节：

```
1. HTTP 请求进入
   │  CloudFront → ALB → ECS Fargate
   v
2. ASGI 中间件链
   │  CorrelationMiddleware    → 生成/提取 X-Correlation-ID
   │  AuditMiddleware          → 记录请求元信息（audit 模块）
   │  ExceptionHandler         → 全局异常捕获 → ErrorResponse
   v
3. FastAPI 路由匹配
   │  /api/v1/{module}/{endpoint}
   v
4. 依赖注入 (Depends)
   │  get_current_user()       → JWT 验证 + 用户信息
   │  require_role("admin")    → RBAC 权限检查（可选）
   │  get_db()                 → 异步数据库会话
   │  get_xxx_service()        → 构造 Application Service（注入 Repository + 外部客户端）
   v
5. Application Service 执行业务逻辑
   │  DTO 验证 → 领域规则检查 → Repository CRUD → 领域事件发布
   v
6. EventBus 异步分发
   │  AgentCreatedEvent → audit 模块写入审计日志
   │                    → insights 模块统计计数
   v
7. 响应序列化
   │  Pydantic Response Schema → JSON
   └→ HTTP 200/201/204
```

**SSE 流式请求** (Agent 对话): 步骤 1-4 相同，但第 5 步使用 `StreamingResponse`，Agent SDK 的每个 chunk 通过 SSE 实时推送到客户端。

### 2.3 后端业务模块一览

| 模块 | 职责 | 首次交付 | 端点数 | 关键实体 |
|------|------|:-------:|:------:|---------|
| **shared** | 共享内核 — PydanticEntity 基类、IRepository、EventBus、DomainError、DB session | Phase 1 | - | - |
| **auth** | JWT 认证 + RBAC + SSO/SAML + LDAP + 登录锁定 + Refresh Token | Phase 1 | 10+ | User, Role |
| **agents** | Agent CRUD、状态机 (DRAFT→ACTIVE→ARCHIVED)、AgentConfig、工具绑定 | Phase 1 | 7 | Agent, AgentConfig |
| **execution** | Agent 执行引擎、SSE 流式、Agent Teams、Memory、IAgentRuntime 接口 | Phase 1 | 12+ | Conversation, Message, TeamExecution |
| **tool_catalog** | 企业工具注册 (MCP/API/Function)、5 状态审批流程、Gateway 同步 | Phase 2 | 10 | Tool, ToolApproval |
| **knowledge** | 文档上传、RAG 检索 (Bedrock Knowledge Bases) | Phase 2 | 10 | KnowledgeBase, Document |
| **insights** | Token 归因、使用趋势、CostExplorerAdapter (AWS 真实账单) | Phase 2 | 6 | UsageRecord |
| **templates** | Agent 模板 CRUD、状态机 (DRAFT→PUBLISHED→ARCHIVED)、7 分类、10 预置模板 | Phase 2 | 8 | AgentTemplate |
| **audit** | 审计日志与合规、AuditLog append-only、EventBus 23 事件订阅 + HTTP 中间件 | Phase 4 | 5 | AuditLog |
| **evaluation** | 测试集管理 + 批量评估 + EvalPipeline + BedrockEvalAdapter + EventBridge 定时 | Phase 5 | 14 | TestSuite, TestCase, EvaluationRun |
| **builder** | 对话式 Agent Builder (MCP 驱动)、ClaudeBuilderAdapter、SSE 流式 | Phase 5 | 3 | BuilderSession |
| **billing** | 多租户部门计费 + 预算管理 + ROI 报告 (CostExplorer) | Phase 5 | 10 | Department, Budget, CostRecord |

### 2.4 模块间通信机制

模块间**禁止直接导入**，只有两种合法通信方式：

#### 方式一：EventBus 异步通信（推荐）

适用于"通知"场景 — 发布方不关心订阅方的处理结果。

```python
# 发布方 (agents 模块)
await event_bus.publish_async(AgentCreatedEvent(agent_id=1, owner_id=1))

# 订阅方 (audit 模块)
@event_handler(AgentCreatedEvent)
async def on_agent_created(event: AgentCreatedEvent) -> None:
    await audit_service.log(event)
```

当前系统注册了 **23 种领域事件**，audit 模块订阅所有事件实现全操作审计。

#### 方式二：Querier 同步查询

适用于"查询"场景 — 消费方需要另一模块的数据。

| 接口 | 消费方 | 提供方 | 场景 |
|------|--------|--------|------|
| `IAgentQuerier` | execution | agents | 查询 Agent 是否 ACTIVE |
| `IToolQuerier` | execution | tool_catalog | 查询已审批的工具列表 |
| `IKnowledgeQuerier` | execution | knowledge | 查询关联的知识库 |

三步实现：接口定义在 `shared/domain/interfaces/` → 实现在提供方 `infrastructure/services/` → 组装在 `presentation/api/providers.py` (Composition Root)。

#### 依赖合法性矩阵

| 从 ↓ 导入 → | `shared/*` | `auth.api.deps` | 其他模块 Domain | 其他模块 Service | 其他模块 ORM Model |
|:-------------|:----------:|:---------------:|:--------------:|:---------------:|:-----------------:|
| **Domain** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Application** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Infrastructure** | ✅ | ❌ | ❌ | ❌ | ⚠️ 仅外键 |
| **API** | ✅ | ✅ | ❌ | ❌ | ❌ |

**唯一例外**: `auth.api.dependencies` 的认证依赖（`get_current_user`）可被其他模块 API 层导入。

### 2.5 数据模型概要

```
┌──────────┐       1:N       ┌──────────┐       1:N       ┌──────────────┐
│   User   │ ──────────────> │   Agent  │ ──────────────> │ Conversation │
│  (auth)  │                 │ (agents) │                 │ (execution)  │
└──────────┘                 └────┬─────┘                 └──────┬───────┘
     │                            │                              │
     │                            │ N:N (AgentTool)              │ 1:N
     │                            v                              v
     │                     ┌──────────┐                   ┌──────────┐
     │                     │   Tool   │                   │  Message │
     │                     │(tool_cat)│                   │(execution)│
     │                     └──────────┘                   └──────────┘
     │
     │  1:N (Department)   ┌──────────────┐
     v                     │KnowledgeBase │    N:N with Agent
┌──────────────┐           │ (knowledge)  │◄────────────────┐
│  Department  │           └──────────────┘                 │
│  (billing)   │                                      ┌─────┴────┐
└──────────────┘    ┌──────────────┐  instantiate      │   Agent  │
                    │   Template   │ ────────────────> │          │
                    │ (templates)  │                   └──────────┘
                    └──────────────┘

┌──────────────┐  EventBus 订阅   ┌───────────────────┐
│   AuditLog   │ ◄─────────────── │ All Domain Events │
│   (audit)    │   (23 种事件)     │                   │
└──────────────┘                  └───────────────────┘

┌──────────────┐              ┌────────────────┐
│   TestSuite  │  批量评估     │ EvaluationRun  │
│  + TestCase  │ ──────────>  │ + EvalResult   │
│ (evaluation) │              │ (evaluation)   │
└──────────────┘              └────────────────┘

┌──────────────────────┐
│   TeamExecution      │  Agent Teams 异步多 Agent 协作
│   + TeamExecutionLog │
│   (execution)        │
└──────────────────────┘
```

**关键关系**:
- User 1:N Agent: 用户拥有 Agent
- Agent 1:N Conversation 1:N Message: 对话执行链
- Agent N:N Tool: 通过 AgentTool 关联表绑定工具
- Agent N:N KnowledgeBase: Agent 可关联多个知识库用于 RAG
- Template → Agent: 模板实例化创建 Agent
- AuditLog 订阅所有 23 种 DomainEvent: 全操作审计
- Department 1:N User: 部门隔离，计费归属

### 2.6 前端页面与 Features 概览

#### 15 个页面

| 页面 | 路由 | 功能 |
|------|------|------|
| login | `/login` | 登录 |
| register | `/register` | 注册 |
| dashboard | `/` | 仪表盘概览 |
| agents | `/agents` | Agent 列表与管理 |
| chat | `/chat/:id` | 单 Agent 对话（SSE 流式） |
| team-executions | `/team-executions` | Agent Teams 任务管理 |
| tools | `/tools` | 工具目录管理 |
| knowledge | `/knowledge` | 知识库管理 |
| templates | `/templates` | 模板管理 |
| insights | `/insights` | 使用分析与成本归因 |
| evaluation | `/evaluation` | 评估管理 |
| builder | `/builder` | 对话式 Agent Builder |
| billing | `/billing` | 计费管理 |
| admin | `/admin` | 管理员面板 |
| not-found | `*` | 404 页面 |

#### 12 个 Features

每个 Feature 遵循标准 slice 结构: `api/` (queries + mutations) + `model/` (store + types) + `ui/` (组件) + `lib/` (工具函数)

`auth` / `agents` / `execution` / `team-executions` / `tool-catalog` / `knowledge` / `templates` / `insights` / `evaluation` / `builder` / `billing` / `dashboard`

#### SSE 流式通信三层架构

Agent 对话和 Teams 执行使用 SSE 流式通信：

```
Layer 3: Feature Stream Hook (features/*/api/stream.ts)
         useRef<AbortController> + Zustand 流式状态管理
         finally 块 invalidateQueries 刷新缓存
         ─────────────────────────────────────────
Layer 2: Feature 适配器 (features/*/lib/sse.ts)
         指定 chunk 类型 + HTTP 方法，yield* 委托 shared
         ─────────────────────────────────────────
Layer 1: Shared 解析器 (shared/lib/parseSSEStream.ts)
         泛型 async function* 生成器，buffer/line splitting
```

### 2.7 CDK Stack 体系

#### 部署依赖关系

```
NetworkStack → SecurityStack → DatabaseStack → ComputeStack → AgentCoreStack
                                                                    │
                                                        FrontendStack (独立)
                                                        BillingStack  (独立)
                                                        MonitoringStack (最后)
```

#### Stack 概览

| Stack | 命名模式 | 关键资源 |
|-------|---------|---------|
| **NetworkStack** | `ai-agents-plat-network-{env}` | VPC (3 AZ)、Public/Private/Isolated 子网、NAT Gateway、S3 VPC Endpoint |
| **SecurityStack** | `ai-agents-plat-security-{env}` | Security Groups (API/DB)、KMS Key、JWT Secret (Secrets Manager) |
| **DatabaseStack** | `ai-agents-plat-database-{env}` | Aurora MySQL 3.10.0、S3 Knowledge Bucket、DB 密码 (Secrets Manager) |
| **ComputeStack** | `ai-agents-plat-compute-{env}` | ECS Fargate (Task Definition + Service)、ALB、Auto Scaling |
| **AgentCoreStack** | `ai-agents-plat-agentcore-{env}` | ECR (Agent 镜像)、AgentCore Runtime (2 AZ)、AgentCore Gateway (MCP)、Cognito |
| **FrontendStack** | `ai-agents-plat-frontend-{env}` | S3 Private Bucket + CloudFront OAC |
| **BillingStack** | `ai-agents-plat-billing-{env}` | AWS Budgets 月度告警 (Dev $100, Prod $1000) |
| **MonitoringStack** | `ai-agents-plat-monitoring-{env}` | CloudWatch Alarms + Dashboard、SNS 告警 |

#### 网络分层

| 子网层 | 用途 | 典型资源 |
|--------|------|---------|
| **PUBLIC** | 面向互联网 | ALB、NAT Gateway |
| **PRIVATE_WITH_EGRESS** | 有出站网络 | ECS Fargate、AgentCore Runtime |
| **PRIVATE_ISOLATED** | 无外网访问 | Aurora MySQL |

---

## 3. 后端模块开发指南

### 3.1 四层结构详解

每个业务模块内部严格遵循四层结构，依赖方向从外向内：

```
┌──────────────────────────────────────────────────────────┐
│                   API Layer (表现层)                       │
│  endpoints.py — FastAPI router                            │
│  schemas/requests.py + responses.py — Pydantic I/O 模型    │
│  dependencies.py — 依赖注入函数                             │
├──────────────────────────────────────────────────────────┤
│               Application Layer (应用层)                   │
│  services/{entity}_service.py — 业务用例编排                │
│  dto/ — 内部数据传输对象 (dataclass)                        │
│  interfaces/ — 模块内外部服务抽象 (如 IS3Client)             │
│  exceptions/ — 应用层异常                                   │
├──────────────────────────────────────────────────────────┤
│                 Domain Layer (领域层)                       │
│  entities/{entity}.py — 领域实体 (PydanticEntity)           │
│  value_objects/ — 值对象 (frozen dataclass)                 │
│  repositories/{entity}_repository.py — 仓储接口              │
│  events.py — 领域事件定义                                    │
│  exceptions.py — 领域异常                                    │
├──────────────────────────────────────────────────────────┤
│             Infrastructure Layer (基础设施层)               │
│  persistence/models/{entity}_model.py — ORM 模型            │
│  persistence/repositories/{entity}_repository_impl.py      │
│  external/{service}_adapter.py — 外部服务适配器              │
└──────────────────────────────────────────────────────────┘
```

**依赖规则**:

| 层级 | 可以依赖 | 禁止依赖 |
|------|---------|---------|
| Domain | Pydantic（数据验证）、`shared/domain` | FastAPI, SQLAlchemy, boto3 |
| Application | Domain 层 | FastAPI, SQLAlchemy, boto3 |
| Infrastructure | Domain + Application | - |
| API | Application + Domain（类型） | Infrastructure（通过 DI 解耦） |

### 3.2 新模块开发步骤

以创建一个名为 `example` 的新模块为例：

#### Step 1: 创建目录结构

```
backend/src/modules/example/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── endpoints.py
│   ├── dependencies.py
│   └── schemas/
│       ├── __init__.py
│       ├── requests.py
│       └── responses.py
├── application/
│   ├── __init__.py
│   ├── dto/
│   │   └── __init__.py
│   ├── interfaces/
│   │   └── __init__.py
│   └── services/
│       ├── __init__.py
│       └── example_service.py
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   └── example.py
│   ├── value_objects/
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── example_repository.py
│   ├── events.py
│   └── exceptions.py
└── infrastructure/
    ├── __init__.py
    └── persistence/
        ├── __init__.py
        ├── models/
        │   ├── __init__.py
        │   └── example_model.py
        └── repositories/
            ├── __init__.py
            └── example_repository_impl.py
```

#### Step 2: 定义领域实体

```python
# domain/entities/example.py
from src.shared.domain import PydanticEntity
from pydantic import ConfigDict

class Example(PydanticEntity):
    """示例实体。"""
    model_config = ConfigDict(validate_assignment=True)

    name: str
    description: str
    status: str = "draft"
    owner_id: int

    def activate(self) -> None:
        if self.status != "draft":
            raise InvalidStateTransitionError("Example", self.status, "active")
        self.status = "active"
        self.touch()  # 更新 updated_at
```

#### Step 3: 定义仓储接口

```python
# domain/repositories/example_repository.py
from src.shared.domain import IRepository
from src.modules.example.domain.entities.example import Example

class IExampleRepository(IRepository[Example, int]):
    """示例仓储接口。"""
    pass
```

#### Step 4: 实现 Application Service

```python
# application/services/example_service.py
from dataclasses import dataclass

@dataclass
class CreateExampleDTO:
    name: str
    description: str

class ExampleService:
    """示例业务服务。"""
    def __init__(self, repository: IExampleRepository) -> None:
        self._repository = repository

    async def create(self, dto: CreateExampleDTO, user_id: int) -> Example:
        example = Example(name=dto.name, description=dto.description, owner_id=user_id)
        created = await self._repository.create(example)
        await event_bus.publish_async(ExampleCreatedEvent(example_id=created.id, owner_id=user_id))
        return created
```

#### Step 5: 实现 Infrastructure 层

```python
# infrastructure/persistence/models/example_model.py
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.infrastructure.persistence.base import Base

class ExampleModel(Base):
    __tablename__ = "examples"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
```

```python
# infrastructure/persistence/repositories/example_repository_impl.py
from src.shared.infrastructure import PydanticRepository

class ExampleRepositoryImpl(PydanticRepository[Example, ExampleModel, int]):
    _entity_class = Example
    _model_class = ExampleModel
    _updatable_fields = {"name", "description", "status"}  # 白名单控制可更新字段
```

#### Step 6: 暴露 API 端点

```python
# api/endpoints.py
from fastapi import APIRouter, Depends
router = APIRouter(prefix="/api/v1/examples", tags=["examples"])

@router.post("", status_code=201, response_model=ExampleResponse)
async def create_example(
    request: CreateExampleRequest,
    current_user: CurrentUserDep,
    service: ExampleService = Depends(get_example_service),
) -> ExampleResponse:
    dto = CreateExampleDTO(name=request.name, description=request.description)
    example = await service.create(dto, current_user.id)
    return ExampleResponse.from_entity(example)
```

#### Step 7: 注册路由

在 `presentation/api/providers.py` 中注册依赖注入，在 `presentation/api/main.py` 中挂载 router。

### 3.3 数据模型选择指南

| 层级 | 组件类型 | 推荐方案 | 理由 |
|------|---------|---------|------|
| Domain | Entity | Pydantic (PydanticEntity) | 业务规则验证、状态可变 |
| Domain | Value Object | `@dataclass(frozen=True)` | 不可变、相等性基于值 |
| Application | DTO | `@dataclass` | 内部传输、已验证数据 |
| Infrastructure | ORM Model | SQLAlchemy Mapped | 持久化专用 |
| Infrastructure | 外部响应 | Pydantic | 需验证和类型转换 |
| API | Request/Response | Pydantic BaseModel | 外部输入验证、FastAPI 集成 |

**快速决策流程**:

```
数据来自外部？ ──是──► Pydantic
      │
     否 → 需要业务验证？ ──是──► Pydantic
      │
     否 → 需要不可变？ ──是──► dataclass(frozen=True)
      │
     否 → dataclass
```

### 3.4 异常处理体系

所有领域异常定义在 `shared/domain/exceptions.py`，由 `shared/api/exception_handlers.py` 自动映射 HTTP 状态码：

| 异常类型 | HTTP 状态码 | 使用场景 |
|---------|:-----------:|---------|
| `EntityNotFoundError` | 404 | 资源不存在 |
| `DuplicateEntityError` | 409 | 资源已存在 |
| `InvalidStateTransitionError` | 409 | 状态转换非法（如 ACTIVE Agent 不能直接删除） |
| `ValidationError` | 422 | 参数验证失败 |
| `ResourceQuotaExceededError` | 429 | 配额不足 |

**SDK 异常转换模式**: 在 Infrastructure 层将 SDK 原始异常转换为领域异常：

```python
try:
    self._client.operation(...)
except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchKey":
        raise EntityNotFoundError("S3Object", key) from e
    raise
```

### 3.5 代码风格速查

| 规则 | 示例 |
|------|------|
| 类型提示必须完整 | `def get_user(user_id: int) -> User \| None:` |
| 使用 `X \| None` 而非 `Optional[X]` | `name: str \| None = None` |
| 使用内置泛型 | `list[str]`, `dict[str, int]` |
| 禁止 `Any` 类型 | 使用 `TypeVar` 或具体类型替代 |
| 函数单行签名（≤120 字符） | 不要将每个参数单独换行 |
| Docstring 遵循"类型即文档" | 类型自解释时省略，有副作用/异常时说明 |
| 并发执行独立任务 | `await asyncio.gather(task1(), task2())` |

### 3.6 日志规范

使用 **structlog** 结构化日志：

```python
import structlog
logger = structlog.get_logger(__name__)

# ✅ 结构化键值对
logger.info("user_created", user_id=user.id, email=mask_email(user.email))

# ❌ 禁止字符串拼接
logger.info(f"创建用户 {user.id}")

# ❌ 禁止 print
print("debug info")
```

**脱敏规则**: 密码完全隐藏 `"****"` | Token 保留前 4 位 `"sk-1****"` | 邮箱部分隐藏 `"z***@example.com"`

**Correlation ID**: 通过 `X-Correlation-ID` Header 自动在 structlog contextvars 中注入，贯穿整个请求链路。

### 3.7 数据库迁移 (Alembic)

```bash
# 创建新迁移（基于 ORM Model 变更自动生成）
cd backend && uv run alembic revision --autogenerate -m "add_examples_table"

# 执行迁移（升级到最新版本）
uv run alembic upgrade head

# 回滚上一个版本
uv run alembic downgrade -1

# 查看当前版本
uv run alembic current

# 查看迁移历史
uv run alembic history --verbose
```

**注意事项**:
- 自动生成后**必须人工检查**迁移脚本，Alembic 不能检测所有变更（如列重命名）
- MySQL TEXT 列**不支持** `server_default`，默认值只能在 Python 层设置
- 新表必须先创建迁移脚本再运行测试，否则集成测试会因为表不存在而失败

### 3.8 PR 预提交检查

```bash
# 一键验证（提交前必跑）
uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/ && uv run pytest --cov=src --cov-fail-under=85
```

| 检查项 | 命令 |
|--------|------|
| 代码检查 | `uv run ruff check src/` |
| 格式检查 | `uv run ruff format --check src/` |
| 类型检查 | `uv run mypy src/` |
| 测试 + 覆盖率 | `uv run pytest --cov=src --cov-fail-under=85` |
| 安全扫描 | `uv run bandit -r src/` |
| 依赖漏洞 | `uv run pip-audit` |
| 架构合规 | `uv run pytest tests/unit/test_architecture_compliance.py -v` |

---

## 4. 前端模块开发指南

### 4.1 FSD 分层架构

前端采用 **Feature-Sliced Design (FSD)**，核心规则是**只能向下依赖，不能向上或平级依赖**。

#### 分层依赖矩阵

| 从 ↓ 导入 → | shared | entities | features | widgets | pages | app |
|:-------------|:------:|:--------:|:--------:|:-------:|:-----:|:---:|
| **app** | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| **pages** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **widgets** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **features** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **entities** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **shared** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

#### 各层职责

| 层级 | 职责 | 典型内容 | 禁止 |
|------|------|---------|------|
| **app** | 应用初始化 | App.tsx、routes、providers (Query/Auth) | 具体业务实现 |
| **pages** | 页面组装 | 组合 widgets + features，页面布局 | 业务逻辑 |
| **widgets** | 独立 UI 块 | Header、Sidebar、UserMenu | API 调用 |
| **features** | 业务功能 | LoginForm、AgentList、ChatInterface | 跨 feature 依赖 |
| **entities** | 数据模型 | User/Agent 类型定义 + AgentCard 基础 UI | 复杂业务逻辑 |
| **shared** | 共享工具 | Button、Input、API Client、hooks、utils | 任何业务逻辑 |

### 4.2 Feature Slice 标准结构

每个 Feature 遵循统一的 Slice 结构：

```
features/{feature}/
├── index.ts              # 公开 API 导出（唯一入口）
├── api/
│   ├── queries.ts        # React Query hooks (useAgents, useCreateAgent)
│   └── stream.ts         # SSE 流式 Hook（对话/Teams 专用）
├── model/
│   ├── store.ts          # Zustand store
│   └── types.ts          # TypeScript 类型定义
├── ui/
│   ├── {Component}.tsx   # UI 组件
│   └── {Component}.test.tsx  # 单元测试（与组件同目录）
└── lib/
    ├── utils.ts          # 工具函数
    └── sse.ts            # SSE 适配器（可选）
```

### 4.3 状态管理策略

| 数据类型 | 方案 | 位置 |
|---------|------|------|
| 服务端数据 (Agent 列表/详情) | TanStack Query (React Query) | `features/*/api/queries.ts` |
| 全局 UI 状态 (主题/侧边栏) | Zustand | `shared/store/` |
| 用户会话 (Token/登录状态) | Zustand (内存，**禁止** localStorage) | `features/auth/model/store.ts` |
| 表单状态 | React Hook Form + Zod | 组件内 |
| 组件局部状态 | useState / useReducer | 组件内 |

**React Query Key Factory 模式**:

```typescript
export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (filters: AgentFilters) => [...agentKeys.lists(), filters] as const,
  detail: (id: string) => [...agentKeys.all, 'detail', id] as const,
};
```

### 4.4 组件设计规范

| 组件类型 | 位置 | 特点 |
|---------|------|------|
| **展示型** (Button, Card) | `shared/ui/` | 纯 UI，无状态，`forwardRef` + `displayName` |
| **容器型** (AgentList) | `features/*/ui/` | React Query 数据获取 + loading/error/empty 三态 |
| **复合型** (Tabs, Dialog) | `shared/ui/` | Context 共享状态 + `Object.assign` 组合导出 |

**Props 设计规则**:
- 使用 `interface`（非 `type`）
- 事件 Props 以 `on` 开头，处理函数以 `handle` 开头
- 继承原生属性：`extends React.ButtonHTMLAttributes<HTMLButtonElement>`

### 4.5 SSE 流式通信

Agent 对话和 Teams 执行使用三层 SSE 架构：

| 层 | 文件 | 职责 |
|----|------|------|
| **Layer 1** | `shared/lib/parseSSEStream.ts` | 泛型 `async function*` 生成器，buffer/line splitting |
| **Layer 2** | `features/*/lib/sse.ts` | 指定 chunk 类型 + HTTP 方法，`yield*` 委托 shared |
| **Layer 3** | `features/*/api/stream.ts` | `useRef<AbortController>` 生命周期 + Zustand 流式状态 |

**关键约定**: SSE 不使用 React Query mutation | Token 由调用方传入 | 组件卸载时 `AbortController.abort()`

### 4.6 前端 PR 检查

```bash
# 一键验证（提交前必跑）
pnpm lint && pnpm format:check && pnpm typecheck && pnpm test:coverage
```

---

## 5. 基础设施与 CDK 开发指南

### 5.1 CDK Construct 分层

| 层级 | 描述 | 来源 | 使用时机 |
|------|------|------|---------|
| **L1** | CloudFormation 直接映射 | `Cfn*` 前缀 | L2 不支持时才用 |
| **L2** | 高级抽象 + 合理默认值 | `aws-*` 模块 | **优先使用** |
| **L3** | 业务组合，多资源协作 | 自定义 Construct | 需要组合多个 L2 时 |

### 5.2 Stack 设计模式

**Stack Props 模式**:

```typescript
export interface ComputeStackProps extends cdk.StackProps {
  readonly vpc: ec2.IVpc;                    // 必需依赖
  readonly instanceType?: ec2.InstanceType;  // 可选配置（解构时设默认值）
}
```

**Stack 间依赖通过 Props 传递**:

```typescript
// bin/app.ts
const networkStack = new NetworkStack(app, `Network-${env}`);
const computeStack = new ComputeStack(app, `Compute-${env}`, {
  vpc: networkStack.vpc,
});
computeStack.addDependency(networkStack);
```

**跨 Stack 通信优先级**: Props 传递（首选） → SSM Parameter（跨 App） → CfnOutput（不推荐）

### 5.3 Construct 设计规范

```typescript
export interface VpcConstructProps {
  readonly vpcCidr: string;
  readonly maxAzs?: number;  // @default 3
}

/**
 * VPC Construct — 创建三层子网 VPC。
 * @remarks 默认 3 AZ，含 NAT Gateway
 */
export class VpcConstruct extends Construct {
  public readonly vpc: ec2.Vpc;

  constructor(scope: Construct, id: string, props: VpcConstructProps) {
    super(scope, id);
    const { vpcCidr, maxAzs = 3 } = props;
    this.vpc = new ec2.Vpc(this, 'Vpc', { /* ... */ });
  }
}
```

**安全默认配置**:

| 资源 | 必须配置 |
|------|---------|
| S3 | `encryption: S3_MANAGED` + `blockPublicAccess: BLOCK_ALL` + `enforceSSL: true` |
| RDS | `storageEncrypted: true` + `deletionProtection: true` + `PRIVATE_ISOLATED` 子网 |
| IAM | 使用 Grant 方法（`bucket.grantRead(fn)`），**禁止** `actions: ['*']` |

### 5.4 环境配置

通过 CDK Context 管理环境差异:

```bash
pnpm cdk deploy --all --context env=dev    # Dev 环境
pnpm cdk deploy --all --context env=prod   # Prod 环境（需审批）
```

| 维度 | Dev | Prod |
|------|-----|------|
| ECS | 256 CPU / 512 MiB / 1 任务 | 512 CPU / 1024 MiB / 2 任务 |
| Aurora | db.t3.medium, 单实例 | db.r6g.large, Writer + Reader (多 AZ) |
| NAT Gateway | 1 个 | 每 AZ 一个 |
| RemovalPolicy | DESTROY | RETAIN (S3) / SNAPSHOT (RDS) |
| 日志保留 | 1 周 | 1 年 |

### 5.5 CDK 测试策略

| 类型 | 用途 | 工具 |
|------|------|------|
| **Fine-grained** | 验证特定资源属性 | CDK Assertions (`hasResourceProperties`) |
| **Snapshot** | 检测意外变更 | Jest Snapshot (`toMatchSnapshot`) |
| **Compliance** | 安全合规检查 | CDK Nag (`AwsSolutionsChecks`) |

```bash
pnpm test                    # 运行所有测试
pnpm test:coverage           # 测试 + 覆盖率（目标 ≥85%）
pnpm test -- -u              # 更新快照
```

### 5.6 CDK PR 检查

```bash
# 一键验证（提交前必跑）
pnpm lint && pnpm format:check && pnpm typecheck && pnpm cdk synth && pnpm test:coverage
```

---

## 6. API 参考文档

### 6.1 API 概览

**Base URL**: `{VITE_API_BASE_URL}/api/v1`

**认证**: 除 `/auth/login` 和 `/auth/register` 外，所有端点需要 `Authorization: Bearer {token}` Header。

**交互式 API 文档**: 启动后端后访问 `http://localhost:8000/docs`（Swagger UI）或 `http://localhost:8000/redoc`（ReDoc），可查看所有端点的完整请求/响应 Schema 并在线测试。

**通用响应格式**:

```json
// 成功（列表）
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}

// 错误
{
  "code": "NOT_FOUND_AGENT",
  "message": "Agent 不存在",
  "details": null
}
```

### 6.2 认证模块 (auth)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录获取 Token |
| POST | `/auth/register` | 注册新用户 |
| POST | `/auth/refresh` | 刷新 Token |
| GET | `/auth/me` | 获取当前用户信息 |
| PUT | `/auth/me` | 更新当前用户信息 |
| PUT | `/auth/me/password` | 修改密码 |

**登录示例**:

```bash
curl -X POST ${API_URL}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","password":"Admin@2026!"}'

# 响应
{"access_token":"eyJ...","refresh_token":"eyJ...","token_type":"bearer"}
```

### 6.3 Agent 管理 (agents)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/agents` | 获取 Agent 列表（支持分页） |
| POST | `/agents` | 创建 Agent（状态为 DRAFT） |
| GET | `/agents/{id}` | 获取 Agent 详情 |
| PUT | `/agents/{id}` | 更新 Agent 配置 |
| POST | `/agents/{id}/activate` | 激活 Agent (DRAFT→ACTIVE) |
| POST | `/agents/{id}/archive` | 归档 Agent (ACTIVE→ARCHIVED) |
| DELETE | `/agents/{id}` | 删除 Agent（仅 DRAFT 状态） |

### 6.4 对话执行 (execution)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/conversations` | 创建对话 |
| GET | `/conversations` | 获取对话列表 |
| GET | `/conversations/{id}` | 获取对话详情 + 消息历史 |
| POST | `/conversations/{id}/messages/stream` | 发送消息（SSE 流式响应） |
| DELETE | `/conversations/{id}` | 删除对话 |

**SSE 流式对话示例**:

```bash
curl -N -X POST ${API_URL}/api/v1/conversations/1/messages/stream \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content":"帮我写一个 Python 排序函数"}'

# SSE 响应流
data: {"type":"text","content":"好的"}
data: {"type":"text","content":"，以下是"}
data: {"type":"tool_use","name":"code_editor","input":{...}}
data: {"type":"done","usage":{"input_tokens":150,"output_tokens":300}}
```

### 6.5 Agent Teams (execution)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/team-executions` | 创建 Teams 任务 |
| GET | `/team-executions` | 获取 Teams 任务列表 |
| GET | `/team-executions/{id}` | 获取 Teams 任务详情 |
| GET | `/team-executions/{id}/stream` | SSE 订阅执行进度 |
| POST | `/team-executions/{id}/cancel` | 取消执行 |

### 6.6 工具目录 (tool_catalog)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/tools` | 获取工具列表 |
| POST | `/tools` | 注册工具 (DRAFT) |
| GET | `/tools/{id}` | 获取工具详情 |
| PUT | `/tools/{id}` | 更新工具配置 |
| POST | `/tools/{id}/submit-review` | 提交审批 |
| POST | `/tools/{id}/approve` | 审批通过（需 admin） |
| POST | `/tools/{id}/reject` | 审批拒绝（需 admin） |

**工具审批流程**: `DRAFT → PENDING_REVIEW → APPROVED / REJECTED`

### 6.7 其他模块端点摘要

| 模块 | 前缀 | 核心端点 |
|------|------|---------|
| knowledge | `/knowledge-bases` | CRUD + 文档上传 + RAG 检索 |
| templates | `/templates` | CRUD + 实例化为 Agent |
| insights | `/insights` | 使用统计 + 成本归因 |
| evaluation | `/evaluations` | 测试集 CRUD + 批量执行 + Pipeline |
| builder | `/builder` | 对话式创建 Agent (SSE) |
| billing | `/departments` + `/budgets` | 部门管理 + 预算配额 + ROI |
| audit | `/audit-logs` | 审计日志查询（只读） |

### 6.8 HTTP 状态码约定

| 状态码 | 场景 |
|--------|------|
| 200 | 成功 (GET, PUT) |
| 201 | 创建成功 (POST) |
| 204 | 删除成功 (DELETE) |
| 400 | 请求参数错误 |
| 401 | 未认证（Token 无效或过期） |
| 403 | 无权限（角色不足） |
| 404 | 资源不存在 |
| 409 | 资源冲突 / 状态转换非法 |
| 422 | 验证错误 |
| 429 | 配额超限 / 登录锁定 |

---

## 7. 测试策略深度指南

### 7.1 TDD 工作流

本项目全面采用测试驱动开发：

```
1. 🔴 Red:    先写一个失败的测试
2. 🟢 Green:  编写最少代码使测试通过
3. 🔄 Refactor: 重构代码，保持测试通过
```

**测试诚信原则**: 切勿为让测试通过而伪造结果。测试失败 = 代码有问题，必须修复代码。

### 7.2 覆盖率要求

| 子项目 | 整体最低 | 整体目标 | 分层要求 |
|--------|:-------:|:-------:|---------|
| **后端** | 85% | 90% | Domain 95% / Application 90% / Infrastructure 80% / API 80% |
| **前端** | 80% | 85% | Hooks 90% / Components 80% / Utils 95% |
| **CDK** | 85% | 90% | Constructs 90% / Stacks 85% |

### 7.3 后端测试策略

#### 测试分层

| 层级 | 目录 | 覆盖范围 | Mock 策略 | 速度 |
|------|------|---------|----------|------|
| **Unit** | `tests/modules/{m}/unit/` | Entity、Service、领域逻辑 | Mock 外部依赖 (Repo, SDK) | ms |
| **Integration** | `tests/modules/{m}/integration/` | API 端点、仓库实现 | SQLite (默认) / MySQL (`--mysql`) | s |
| **E2E** | `tests/e2e/` | 跨模块完整流程 | 无 | min |

#### 标准 Fixture 三件套

每个模块的 `conftest.py` 统一提供：

1. `mock_{entity}_repo` — `AsyncMock(spec=I{Entity}Repository)`
2. `{entity}_service` — 注入 mock repo 的 Service 实例
3. `mock_event_bus` — patch event_bus 为 AsyncMock，避免事件副作用

#### 双引擎测试

```bash
uv run pytest                # SQLite (默认，毫秒级)
uv run pytest --mysql        # MySQL (需 docker mysql-test 容器)
```

#### 测试命名规范

```python
# 文件: test_{component}.py
# 类:   Test{Class}
# 方法: test_{method}_{scenario}_{expected}

class TestUserService:
    def test_create_with_valid_dto_returns_user(self) -> None: ...
    def test_create_with_duplicate_email_raises(self) -> None: ...
```

#### 测试模式

```python
# AAA 模式 (Arrange-Act-Assert)
def test_create_user_returns_user(self) -> None:
    dto = CreateUserDTO(name="张三", email="a@b.com")   # Arrange
    result = service.create_user(dto)                    # Act
    assert result.name == "张三"                         # Assert

# 异常测试
with pytest.raises(ValidationError, match="名称不能为空"):
    service.create_user(invalid_dto)

# 参数化
@pytest.mark.parametrize("status,expected", [("draft", True), ("active", False)])
def test_can_delete(self, status: str, expected: bool) -> None: ...
```

### 7.4 前端测试策略

#### 测试分层

| 层级 | 工具 | Mock | 查询优先级 |
|------|------|------|-----------|
| **Unit** | Vitest + Testing Library | 外部依赖 | `getByRole` > `getByLabelText` > `getByText` > `getByTestId` |
| **Integration** | Vitest + MSW | 外部 API (MSW Mock) | 同上 |
| **E2E** | Playwright | 无 | Page Object 模式 |

#### MSW API Mock

```typescript
// tests/mocks/handlers.ts
export const handlers = [
  http.get('/api/v1/agents', () => HttpResponse.json([{ id: '1', name: 'Agent 1' }])),
];

// tests/setup.ts
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

#### Playwright E2E (Page Object)

```typescript
export class LoginPage {
  constructor(private page: Page) {}
  async login(email: string, password: string) {
    await this.page.getByLabel('邮箱').fill(email);
    await this.page.getByLabel('密码').fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
  }
}
```

### 7.5 CDK 测试策略

| 测试类型 | 用途 | 示例 |
|---------|------|------|
| **Fine-grained** | 验证资源属性 | `template.hasResourceProperties('AWS::S3::Bucket', { ... })` |
| **Snapshot** | 检测意外变更 | `expect(template.toJSON()).toMatchSnapshot()` |
| **CDK Nag** | 安全合规 | `Aspects.of(stack).add(new AwsSolutionsChecks())` |

### 7.6 架构合规测试

后端有专门的架构合规测试，验证分层依赖方向和模块隔离：

```bash
uv run pytest tests/unit/test_architecture_compliance.py -v
```

验证内容：Domain 层绝对隔离 | Application 层依赖接口 | Auth 依赖例外 | 模块 Domain 层不导入其他模块。

---

## 8. 部署与环境管理

### 8.1 环境策略

| 环境 | 用途 | 部署方式 | 审批 |
|------|------|---------|------|
| **Dev** | 开发 + 验证 | CI 自动 / 手动 | 无 |
| **Prod** | 生产 | CI 手动触发 | 需人工审批 |

> 当前仅 Dev + Prod 两套环境（v1.4 简化），Staging 暂不实现。Prod 部署前通过 `cdk diff` 审查配置差异。

### 8.2 CI/CD Pipeline 概览

#### PR 触发（质量门控）

| 工作流 | 触发条件 | 内容 |
|--------|---------|------|
| `backend-ci.yml` | PR 涉及 `backend/` | Ruff + MyPy + pytest (MySQL Service Container) |
| `frontend-ci.yml` | PR 涉及 `frontend/` | ESLint + TypeCheck + Vitest + Build |

#### 部署触发

| 工作流 | 触发条件 | 内容 |
|--------|---------|------|
| `backend-deploy.yml` | push main + `backend/src/` | 质量门控 → Dev 自动 → Prod 手动审批 |
| `frontend-deploy.yml` | push main + `frontend/src/` | 质量门控 → S3 + CloudFront 部署 |
| `cdk-deploy.yml` | push main + `infra/` | test → CDK deploy (dev 自动, prod 需审批) |

#### 运维工作流

| 工作流 | 频率 | 内容 |
|--------|------|------|
| `security-scan.yml` | 每周 | 后端 (bandit + pip-audit) + 前端 (pnpm audit) |
| `performance-test.yml` | 每周 | Locust 性能测试 |
| `backup-verify.yml` | 每月 | Aurora 快照状态检查 |
| `drift-detection.yml` | 每周 | CloudFormation Drift 检测（漂移时创建 Issue） |

### 8.3 部署流程

#### 后端部署

```bash
# 1. 构建镜像
cd backend && docker build --platform linux/amd64 -t ai-agents-platform:latest .

# 2. 推送到 ECR
aws ecr get-login-password | docker login --username AWS --password-stdin ${ECR_URI}
docker tag ai-agents-platform:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

# 3. 强制新部署
aws ecs update-service \
  --cluster ai-agents-plat-compute-{env} \
  --service {SERVICE_NAME} \
  --force-new-deployment
```

> **注意**: Docker 构建必须指定 `--platform linux/amd64`（ECS Fargate 要求），基础镜像使用 ECR Public（避免 Docker Hub 限流）。

#### CDK 部署

```bash
cd infra
pnpm cdk diff --context env={env}            # 查看变更
pnpm cdk deploy --all --context env={env}     # 部署
```

**部署顺序**: NetworkStack → SecurityStack → DatabaseStack → ComputeStack → AgentCoreStack → FrontendStack → BillingStack → MonitoringStack

### 8.4 回滚策略

| 组件 | 回滚方式 |
|------|---------|
| 后端 (ECS) | `aws ecs update-service --task-definition {PREVIOUS_ARN}` |
| CDK | `pnpm cdk deploy --all --context env={env} --rollback` |
| 数据库 | Aurora PITR（时间点恢复）或快照恢复 |
| S3 | S3 版本回滚 (`scripts/dr-s3-rollback.sh`) |

**灾备目标**: RPO < 5 分钟 | RTO < 15 分钟

### 8.5 监控与告警

| 告警 | 条件 | 动作 |
|------|------|------|
| Aurora CPU 高 | > 80% 持续 15min | SNS 通知 |
| ECS CPU/Memory 高 | > 80% 持续 15min | SNS 通知 |
| ALB 不健康主机 | >= 1 | SNS 通知 |
| ALB 5XX 错误 | > 10 次/5min | SNS 通知 |

**SNS Topic**: `ai-agents-platform-alerts-{dev|prod}`

**Health Check**:
- `GET /health` — 存活检查
- `GET /health/ready` — 就绪检查（含数据库连通性）

---

## 9. AgentCore 集成架构解析

### 9.1 双路径架构 (ADR-006)

Agent 执行通过 `IAgentRuntime` 接口抽象，支持两种运行时：

```
ExecutionService
  └── IAgentRuntime (接口)
        │
        ├── ClaudeAgentAdapter (主路径)
        │     └── claude-agent-sdk
        │           └── claude_agent_sdk.query()
        │                 └── fork Claude Code CLI 子进程 (Node.js SEA)
        │                       ├── stdio pipe ↔ Python SDK 进程
        │                       ├── Bedrock Invoke API (HTTPS)
        │                       └── MCP Server 连接
        │
        └── AgentCoreRuntimeAdapter (降级路径)
              └── boto3
                    └── invoke_inline_agent
                          └── AgentCore Runtime 托管容器
```

### 9.2 双模式运行时 (ADR-014)

| 维度 | in_process 模式 | agentcore_runtime 模式 |
|------|----------------|----------------------|
| 执行位置 | ECS 容器内（CLI 子进程） | AgentCore 独立托管容器 |
| 进程隔离 | 无 — CLI 与 API 共享资源 | 完全隔离 |
| 启动延迟 | ~2s (CLI fork) | ~5-10s (容器冷启动) |
| 适用场景 | 开发调试、轻量 Agent | 生产负载、长时间执行、Teams |
| CDK Context | `--context agentRuntimeMode=in_process` | 默认值 |

### 9.3 AgentCore 服务集成

| AgentCore 服务 | 集成状态 | 用途 |
|---------------|---------|------|
| **AgentCore Runtime** | ✅ CDK 部署 (2 AZ) | Agent 独立容器执行环境 |
| **AgentCore Gateway** | ✅ 已部署 (MCP) | MCP 工具统一入口 |
| **AgentCore Memory** | ✅ MCP 桥接 | Agent 跨会话记忆 |
| **AgentCore Observability** | ✅ OpenTelemetry | 分布式追踪、Agent 执行链路 |
| **AgentCore Identity** | 待集成 (M12) | 统一身份和凭证管理 |

### 9.4 MCP 集成三种模式

| 模式 | 说明 | 使用场景 |
|------|------|---------|
| **AgentCore Gateway SSE** | 远程 MCP Server，通过 Gateway 统一入口 | 企业工具目录中注册的工具 |
| **SDK 进程内 MCP Server** | Python 进程内运行的 MCP Server | 平台内置工具 (platform-tools) |
| **Memory MCP Server** | AgentCore Memory 通过 MCP 桥接 | Agent 记忆读写 |

### 9.5 Agent Teams (ADR-008)

Agent Teams 替代了原规划的 DAG 引擎，实现 LLM 自主多 Agent 协作：

- **启用**: 环境变量 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- **内置工具**: TeamCreate, SendMessage, TaskCreate, TaskUpdate, TaskList
- **编排**: Agent 自主决定团队结构和分工（非预定义 DAG）
- **并发控制**: `asyncio.Semaphore(3)` 限制并发 Agent 数
- **状态机**: `PENDING → RUNNING → COMPLETED / FAILED / CANCELLED`

### 9.6 依赖路径说明

```
Agent 执行路径 (LLM 对话 + 工具调用):
  Python → claude-agent-sdk → Claude Code CLI (Node.js SEA) → Bedrock Invoke API
  • 不使用 boto3
  • 认证: AWS 标准凭证链 (IAM Role / 环境变量)
  • 环境变量: CLAUDE_CODE_USE_BEDROCK=1 + AWS_REGION

Platform API 路径 (资源管理 + 降级):
  Python → boto3 → AgentCore Control API / Bedrock KB API / Converse API
  • BedrockLLMClient (降级路径) 使用 Converse API
  • AgentCore 资源管理使用 bedrock-agentcore-control 客户端
```

---

## 10. 常见问题与故障排查

### 10.1 本地开发常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `uv: command not found` | uv 未安装 | `pip install uv` 或 `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| MySQL 连接被拒 | Docker 未启动 | `docker run -d --name mysql-dev -p 3306:3306 -e MYSQL_ROOT_PASSWORD=changeme -e MYSQL_DATABASE=ai_agents_platform mysql:8.0` |
| `ModuleNotFoundError` | 依赖未安装 | `cd backend && uv sync` |
| TypeScript 类型错误 | 依赖过期 | `cd frontend && pnpm install` |
| CDK synth 失败 | Context 缓存过期 | 删除 `cdk.context.json` 后重试 |
| MyPy 报错 `missing stubs` | 缺少类型桩 | `uv run mypy --install-types` |
| 前端 `@/` 路径找不到 | Vite 路径别名未配 | 检查 `vite.config.ts` 和 `tsconfig.json` 中的 paths |

### 10.2 后端服务问题

#### Health Check 失败

```bash
# 1. 检查 ECS 服务状态
aws ecs describe-services --cluster ai-agents-plat-compute-{env} --services {SERVICE_NAME}

# 2. 检查任务日志
aws logs tail /ecs/ai-agents-platform-{env} --follow

# 3. 检查数据库连接
aws rds describe-db-clusters --db-cluster-identifier {CLUSTER_ID} --query 'DBClusters[0].Status'
```

#### Agent 执行超时

```bash
# 检查 AgentCore Runtime 状态
aws bedrock-agent list-agents --query 'agentSummaries[].{Name:agentName,Status:agentStatus}'

# 检查日志中的 agent.execute span
aws logs filter-log-events \
  --log-group-name /ecs/ai-agents-platform-{env} \
  --filter-pattern '"agent.execute"'
```

### 10.3 数据库相关问题

| 问题 | 原因 | 解决 |
|------|------|------|
| MySQL TEXT 列不支持 `server_default` | MySQL 方言限制 | 移除 TEXT 列默认值，仅在 Python 层设置 |
| SQLAlchemy `autocommit` 行为差异 | 写入丢失 | 强制 `session.commit()` + `get_db` auto-commit/rollback |
| SQLite vs MySQL 测试差异 | 方言差异 | 使用 `--mysql` 运行 MySQL 集成测试 |
| Alembic 迁移失败 | TEXT 列默认值 | 查阅 MySQL 方言限制文档 |

### 10.4 容器化与部署问题

| 问题 | 原因 | 解决 |
|------|------|------|
| ARM64 vs AMD64 | ECS Fargate 容器启动失败 | 强制 `--platform linux/amd64` 构建 |
| Docker Hub 拉取限流 | CI/CD 构建失败 | 替换为 ECR Public 镜像源 |
| ECS 健康检查 `curl` 不可用 | 滚动部署失败 | 用 `python -c "import httpx; ..."` 替代 |
| Aurora 实例类型不兼容 | `db.t3.small` 不支持 Aurora 3.10.0 | 升级到 `db.t3.medium` |
| CDK deploy 失败 (中文描述) | SG description 仅限 ASCII | Security Group 描述统一使用英文 |

### 10.5 AgentCore 集成问题

| 问题 | 原因 | 解决 |
|------|------|------|
| AgentCore AZ 限制 | Runtime 不支持所有 AZ | CDK 限定可用 AZ (us-east-1a/1b) |
| CLIConnectionError | Agent SDK 连接不稳定 | 内建重试模式（已验证有效） |
| `@aws-cdk/aws-bedrock-agentcore-alpha` 变更 | alpha 阶段 API 不稳定 | 锁定版本 + 封装层隔离 + L1 CfnResource 降级路径 |

### 10.6 安全检测命令

```bash
# 后端安全扫描
uv run bandit -r src/                    # 代码安全分析
uv run pip-audit                         # 依赖漏洞扫描

# 前端安全扫描
cd frontend && pnpm audit                # 依赖漏洞

# 敏感信息检测
grep -rE "(password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]" backend/src/
```
