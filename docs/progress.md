# 项目进度

> 每次 Claude Code 会话开始时读取此文件。会话结束时更新"当前状态"和"上次会话"。

## 当前状态

- **阶段**: Phase 4 企业成熟 (12-18 月) — **M12 ✅ 已完成**, Phase 4 关闭
- **里程碑**: Phase 4: M10-prep ✅ → M10 ✅ → M11 ✅ → **M12 ✅**
- **变更积压**: Phase 2-3: 24/24 ✅ | Phase 4: 19/19 ✅ | AgentCore P3: 5/5 ✅
- **关键发现**: 无当前阻断项
- **Dev 环境**: 后端 ECS (256 CPU/512 MiB) + 前端 S3 + CORS + Bedrock IAM ✅ | ALB `ai-agents-dev-546356512.us-east-1.elb.amazonaws.com`
- **Prod 环境**: 后端 ECS (512 CPU/1024 MiB/2 任务) + Aurora db.r6g.large (Writer+Reader) ✅ | ALB `ai-agents-prod-1419512933.us-east-1.elb.amazonaws.com`
- **Stack 命名**: `ai-agents-plat-{stack}-{env}` (v1.4 规范化, 12 个 Stack 全部重建)
- **测试**: 后端 1826 测试 + 基础设施 179 测试 + 前端 80+ 测试 = **2085+ 测试**
- **后端模块**: 10 个 (9 业务 + shared) | **前端**: 190 源文件, FSD 架构, 12 页面 + 20 测试文件
- **SDK**: claude-agent-sdk 0.1.35 | bedrock-agentcore 1.3.0
- **环境策略**: Dev (开发+验证) + Prod (生产)，无 Staging (v1.4 简化)
- **下一步**: Phase 4 已关闭。按 `docs/rollout-plan.md` 启动梯度推广 (Wave 1: 10 人种子用户)

## 模块状态

### Phase 1 (0-3 月)

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| `shared` | 已完成 | ai-agents-factory-v1 | PydanticEntity, IRepository, EventBus, DomainError, get_db, get_settings, PydanticRepository, exception_handlers, schemas |
| `auth` | 已完成 | ai-agents-factory-v1 | User, Role, JWT, RBAC, get_current_user, 登录/注册/me 端点, **Rate Limiting + 账户锁定 (C-S1-1)**, **Refresh Token (C-S1-2)**, **安全审计日志 (C-S1-3)**, **注册权限保护 (C-S1-4)** |
| `agents` | 已完成 | ai-agents-factory-v1 | Agent CRUD (7 端点), 状态机 (draft → active → archived), AgentConfig, 领域事件 |
| `execution` | 已完成 | ai-agents-factory-v1 | 单 Agent 对话 (6 端点) + **Agent Teams (6 端点)**, Bedrock ConverseStream, SSE 流式, IAgentQuerier 跨模块, **对话历史滑动窗口 (C-S2-2)**, **Agent 配置 TTL 缓存 (C-S2-4)**, IAgentRuntime + ClaudeAgentAdapter (ADR-006), **TeamExecution 异步执行 + SSE 进度推送 (ADR-008)** |

### Phase 2 (3-6 月)

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| `tool-catalog` | 已完成 | ai-agents-factory-v1 | 工具注册/审批 (10 端点), 5 状态审批流程, MCP Server/API/Function 三类工具 |
| `knowledge` | 已完成 | ai-agents-factory-v1 | 知识库管理, RAG 检索 (Bedrock Knowledge Bases, ADR-005), 10 端点 |
| `insights` | 已完成 | ai-agents-factory-v1 | Token 归因 + 使用趋势 (6 端点), CostExplorerAdapter (AWS 真实账单), MessageReceivedEvent 订阅, 96 测试 |
| `templates` | 已完成 | ai-agents-factory-v1 | Agent 模板管理 (8 端点), 状态机 (DRAFT → PUBLISHED → ARCHIVED), 7 分类, 10 预置模板, 103 测试 |

### Phase 3 (6-12 月)

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| ~~`orchestration`~~ | 取消 | - | ADR-008: Agent Teams 替代，已在 execution 模块实现 |
| `evaluation` | 已完成 | ai-agents-factory-v1 | 测试集 CRUD + 批量评估 + 结果查询 (14 端点), TestSuite/TestCase/EvaluationRun/EvaluationResult, 58 测试 |
| `frontend` | 已完成 | ai-agents-factory-v1 | React 19 + TypeScript + FSD, 160+ 源文件, 13 页面 (覆盖度 ~85%) |

### Phase 4

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| `audit` | 已完成 | ai-agents-factory-v1 | 审计日志与合规 (5 端点), AuditLog append-only, EventBus 23 事件订阅 + HTTP 中间件, 65 测试 |
| ~~`marketplace`~~ | 移除 | - | ADR-007: 内部平台无需市场机制 |
| ~~`analytics`~~ | 降级 | - | ADR-007: 合并为 insights 增强 |

## 基础设施

| CDK Stack | Dev | Prod | 备注 |
|-----------|:---:|:----:|------|
| ai-agents-plat-network-{env} | ✅ | ✅ | VPC (3 AZ), NAT Gateway *1, Flow Log, S3 Endpoint |
| ai-agents-plat-security-{env} | ✅ | ✅ | KMS, API SG, DB SG, JWT Secret; Prod: SM VPC Endpoint |
| ai-agents-plat-database-{env} | ✅ | ✅ | Aurora MySQL 3.10.0; Dev: db.t3.medium 1实例; Prod: db.r6g.large Writer+Reader |
| ai-agents-plat-agentcore-{env} | ✅ | ✅ | ECR + Runtime (2 AZ) + Gateway (MCP), Cognito |
| ai-agents-plat-compute-{env} | ✅ | ✅ | ECS Fargate + ALB (HTTP:80); Dev: 256CPU/512MiB/1任务; Prod: 512CPU/1024MiB/2任务 |
| ai-agents-plat-monitoring-{env} | ✅ | ✅ | CloudWatch Alarms + Dashboard + SNS 告警 |

---

## 当前 Milestone 任务拆解

### M1: 项目脚手架 (第 1-4 周) — ✅ 已完成

> 交付物: 后端 shared + auth 模块完成
> 验收标准: ruff check + mypy + pytest --cov-fail-under=85 全通过
> 验收结果: **254 测试通过，覆盖率 95.04%，ruff/mypy 全通过**

<details>
<summary>展开查看 M1 任务详情</summary>

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | 创建 backend 目录结构 + pyproject.toml + uv sync | 已完成 | - | `rules/project-structure.md` 初始化检查清单 | 2026-02-09 |
| 2 | shared/domain: PydanticEntity 基类 + IRepository 泛型接口 + DomainError 异常体系 | 已完成 | #1 | `rules/architecture.md` §5 DDD 战术模式 | 2026-02-09 |
| 3 | shared/domain: DomainEvent + EventBus (进程内事件总线) | 已完成 | #1 | `rules/architecture.md` §4.2 事件驱动通信 | 2026-02-09 |
| 4 | shared/infrastructure: get_db 数据库会话 + get_settings 配置管理 + PydanticRepository 基类实现 | 已完成 | #2 | `rules/tech-stack.md` + `rules/sdk-first.md` | 2026-02-09 |
| 5 | shared/api: exception_handler 统一异常处理 + 通用 schemas (PageRequest/PageResponse 等) | 已完成 | #2 | `rules/api-design.md` 错误格式 | 2026-02-09 |
| 6 | presentation/api/main.py: FastAPI app 工厂 + health check 端点 + CORS/中间件 | 已完成 | #4, #5 | `rules/observability.md` §1 Health Check | 2026-02-09 |
| 7 | tests: shared 模块单元测试 + 架构合规测试 (模块边界/依赖方向) | 已完成 | #2-#6 | `rules/testing.md` TDD + AAA 模式 | 2026-02-09 |
| 8 | auth/domain: User 实体 + Role 枚举 + IUserRepository 接口 | 已完成 | #2 | `rules/architecture.md` §5 + `rules/security.md` | 2026-02-09 |
| 9 | auth/application: UserService + JWT Token 签发/验证 + 密码哈希 | 已完成 | #4, #8 | `rules/security.md` + `rules/sdk-first.md` | 2026-02-09 |
| 10 | auth/infrastructure: UserRepositoryImpl + SQLAlchemy ORM Model + Alembic migration | 已完成 | #4, #8 | `rules/tech-stack.md` | 2026-02-09 |
| 11 | auth/api: 登录/注册端点 + get_current_user 依赖注入 + RBAC 权限装饰器 | 已完成 | #6, #9, #10 | `rules/api-design.md` + `rules/security.md` | 2026-02-09 |
| 12 | tests: auth 模块单元测试 + 集成测试 (含数据库交互) | 已完成 | #8-#11 | `rules/testing.md` TDD + AAA 模式 | 2026-02-09 |
| 13 | 质量验收: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过 | 已完成 | #1-#12 | `rules/checklist.md` + roadmap.md §2.6 | 2026-02-09 |

</details>

### M2: Agent CRUD (第 5-8 周) — ✅ 已完成

> 交付物: agents 模块 CRUD API 完成，7 个 RESTful 端点，Agent 状态机 (draft → active → archived)
> 验收标准: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过
> 验收结果: **415 测试通过，覆盖率 97.66%，ruff/mypy 全通过，架构合规 15/15 通过**

<details>
<summary>展开查看 M2 任务详情</summary>

#### 领域模型设计摘要

**Agent 实体**: name, description, system_prompt, status(AgentStatus), owner_id, config(AgentConfig)
**AgentStatus 枚举**: DRAFT → ACTIVE → ARCHIVED（归档不可逆）
**AgentConfig 值对象**: model_id, temperature, max_tokens, top_p, stop_sequences（frozen dataclass）

**状态机规则**:
- `activate()`: DRAFT → ACTIVE（需要 name + system_prompt 非空）
- `archive()`: DRAFT/ACTIVE → ARCHIVED（不可逆）
- 仅 DRAFT 状态可物理删除；ACTIVE 需先归档

**API 端点**: POST /agents, GET /agents, GET /agents/{id}, PUT /agents/{id}, DELETE /agents/{id}, POST /agents/{id}/activate, POST /agents/{id}/archive

**权限模型**: ADMIN 可操作所有 Agent；DEVELOPER 仅操作自己的 Agent；VIEWER 只读

#### 任务拆解

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | agents/domain: Agent 实体 + AgentStatus 枚举 + AgentConfig 值对象 + 状态机 (activate/archive) | 已完成 | - | `rules/architecture.md` §5 DDD 战术模式 | 2026-02-09 |
| 2 | agents/domain: 领域事件 (Created/Activated/Archived/Updated/Deleted) + 模块异常 + IAgentRepository 接口 | 已完成 | #1 | `rules/architecture.md` §4.2 事件驱动, §5.4 仓库接口 | 2026-02-09 |
| 3 | agents/application: DTO (Create/Update/Agent/PagedAgent) + AgentService (CRUD + 状态操作 + 权限校验) | 已完成 | #1, #2 | `rules/architecture.md` §5 + `rules/security.md` §2 RBAC | 2026-02-09 |
| 4 | agents/infrastructure: AgentModel ORM + AgentRepositoryImpl + Alembic migration | 已完成 | #2 | `rules/tech-stack.md` + `rules/project-structure.md` | 2026-02-09 |
| 5 | agents/api: Request/Response Schema + dependencies.py 依赖注入链 + endpoints.py (7 个端点) | 已完成 | #3, #4 | `rules/api-design.md` + `rules/security.md` | 2026-02-09 |
| 6 | 模块注册: main.py 路由注册 + agents 异常映射 + __init__.py 模块导出 | 已完成 | #5 | `rules/architecture.md` §6.3 模块导出 | 2026-02-09 |
| 7 | tests: agents 模块单元测试 (Domain 实体/值对象/状态机 + Application Service 全场景) | 已完成 | #1-#3 | `rules/testing.md` TDD + AAA 模式 | 2026-02-09 |
| 8 | tests: agents 模块集成测试 (Repository 数据库交互 + API 端点 + 架构合规测试更新) | 已完成 | #4-#6, #7 | `rules/testing.md` 集成测试 | 2026-02-09 |
| 9 | 质量验收: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过 | 已完成 | #1-#8 | `rules/checklist.md` + roadmap.md §2.6 | 2026-02-09 |

#### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| AgentConfig 存储方式 | ORM 展开为独立列 | 便于查询筛选和索引，避免 JSON blob |
| status 数据库类型 | String(20) | 与 auth 模块 Role 处理方式一致 |
| owner_id 外键 | ORM 层 ForeignKey，Domain 层仅 int | 遵循模块隔离规则 R1 |
| 删除策略 | 仅 DRAFT 可物理删除 | 防止误删正在使用的 Agent |
| 名称唯一性 | 同 owner 下唯一 (联合索引) | 允许不同用户创建同名 Agent |
| archived 可逆性 | 不可逆 | 简化状态机，审计友好；如需重用可复制新建 |

#### 依赖关系图

```
#1 (Domain 实体) ──► #2 (Domain 契约) ──► #3 (Application)
                                    └──► #4 (Infrastructure) ──► #5 (API) ──► #6 (模块注册)
#1-#3 ──► #7 (单元测试)
#4-#7 ──► #8 (集成测试)
#1-#8 ──► #9 (质量验收)
```

</details>

### M3: 端到端演示 (第 9-12 周) — ✅ 已完成

> 交付物: execution 模块完成（单 Agent 对话）+ SSE 流式响应 + 跨模块集成
> 验收标准: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过；用户可与 ACTIVE Agent 对话
> 验收结果: **611 测试通过，覆盖率 94.08%，ruff/mypy 全通过，架构合规全通过**

<details>
<summary>展开查看 M3 任务详情</summary>

#### 领域模型设计摘要

**Conversation 实体**: title, agent_id, user_id, status(ConversationStatus), message_count, total_tokens
**Message 实体**: conversation_id, role(MessageRole), content, token_count（独立实体，非值对象）
**ConversationStatus 枚举**: ACTIVE → COMPLETED / FAILED（不可逆）
**MessageRole 枚举**: USER / ASSISTANT

**核心流程**:
- 创建对话: 校验 Agent ACTIVE 状态 → 创建 Conversation
- 发送消息: 创建 user Message → 加载历史 + system_prompt → 调用 Bedrock ConverseStream → 创建 assistant Message → SSE 流式返回
- 流式策略: 流进行中内存累积，流结束后一次性写数据库

**跨模块集成**: `shared/domain/interfaces/IAgentQuerier` → agents 模块提供 `AgentQuerierImpl` 实现
**外部服务抽象**: `execution/application/interfaces/ILLMClient` → `infrastructure/external/BedrockLLMClient`（基于 boto3 ConverseStream API，封装 < 100 行）

**API 端点**: POST /conversations, GET /conversations, GET /conversations/{id}, POST /conversations/{id}/messages, POST /conversations/{id}/messages/stream, POST /conversations/{id}/complete

#### 任务拆解

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | execution/domain: Conversation 实体 + Message 实体 + ConversationStatus/MessageRole 枚举 + 状态机 (complete/fail) | 已完成 | - | `rules/architecture.md` §5 DDD 战术模式 | 2026-02-09 |
| 2 | execution/domain: 领域事件 (ConversationCreated/MessageSent/MessageReceived/ConversationCompleted) + 模块异常 + IConversationRepository + IMessageRepository | 已完成 | #1 | `rules/architecture.md` §4.2 事件驱动, §5.4 仓库接口 | 2026-02-09 |
| 3 | shared/domain/interfaces: IAgentQuerier 跨模块接口 + ActiveAgentInfo 数据结构 | 已完成 | - | `rules/architecture.md` §3 模块隔离, §4.3 接口位置 | 2026-02-09 |
| 4 | execution/application: ILLMClient 接口 + LLMMessage/LLMResponse/LLMStreamChunk DTO + ExecutionService (create/send/stream/get/list/complete) | 已完成 | #1-#3 | `rules/architecture.md` §5 + `rules/sdk-first.md` | 2026-02-09 |
| 5 | execution/infrastructure/persistence: ConversationModel + MessageModel ORM + Repos 实现 + Alembic migration | 已完成 | #2 | `rules/tech-stack.md` + `rules/project-structure.md` | 2026-02-09 |
| 6 | execution/infrastructure/external: BedrockLLMClient (boto3 converse/converse_stream 薄封装) | 已完成 | #4 | `rules/sdk-first.md` 封装 < 100 行 | 2026-02-09 |
| 7 | agents/infrastructure: AgentQuerierImpl (实现 shared 的 IAgentQuerier) | 已完成 | #3 | `rules/architecture.md` §3 模块隔离 | 2026-02-09 |
| 8 | execution/api: Request/Response Schema + dependencies.py + endpoints.py (6 端点含 SSE 流式) | 已完成 | #4-#7 | `rules/api-design.md` + `rules/security.md` | 2026-02-09 |
| 9 | 模块注册: main.py 路由注册 + execution 异常映射 + settings 新增 Bedrock 配置 | 已完成 | #8 | `rules/architecture.md` §6.3 | 2026-02-09 |
| 10 | tests: execution 模块单元测试 (Domain + Application mock LLM) | 已完成 | #1-#4 | `rules/testing.md` TDD + AAA 模式 | 2026-02-09 |
| 11 | tests: execution 模块集成测试 (Repo + API 端点 + SSE 流式 + 架构合规更新) | 已完成 | #5-#9, #10 | `rules/testing.md` 集成测试 | 2026-02-09 |
| 12 | 质量验收: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过 | 已完成 | #1-#11 | `rules/checklist.md` + roadmap.md §2.6 | 2026-02-09 |

#### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Bedrock API | ConverseStream (非 AgentCore Runtime) | Phase 1 MVP 简化；converse API 成熟稳定；AgentCore 留给 Phase 3 orchestration |
| Message 建模 | 独立实体 + 独立仓库 | 流式消息需逐步更新；独立分页查询；Token 成本归因 |
| system_prompt 存储 | 不存为 Message | 属于 Agent 配置，非对话内容；Bedrock API 分开传递 |
| 跨模块通信 | shared/interfaces/IAgentQuerier | 遵循模块隔离 R1/R3；agents 可独立演进 |
| 流式写数据库 | 流结束后一次性写入 | 减少数据库压力；避免大量短事务 |
| 对话删除 | 不支持物理删除，仅 complete | 审计友好；数据保留用于 insights |
| Token 统计 | Conversation.total_tokens 冗余 + Message.token_count 明细 | 列表查询避免 SUM；支持两个维度归因 |
| LLM 接口参数 | 原始类型（非 AgentConfig） | 避免 Application 层跨模块导入 |
| SSE 格式 | data-only JSON | Phase 1 简化；前端解析简单 |
| boto3 异步 | asyncio.to_thread() 包装 | boto3 同步 SDK，薄封装异步化 |

#### 依赖关系图

```
#1 (Domain 实体) ──► #2 (事件/异常/仓库接口) ──┐
                                                ├──► #4 (Application: ExecutionService + ILLMClient)
#3 (shared IAgentQuerier) ─────────────────────┘        │
                                                ┌───────┼───────┐
                                                ↓       ↓       ↓
                                          #5 (ORM)  #6 (Bedrock) #7 (AgentQuerierImpl)
                                                └───────┼───────┘
                                                        ↓
                                                  #8 (API 端点)
                                                        ↓
                                                  #9 (模块注册)
                                                        ↓
                                          ┌─────────────┼─────────────┐
                                          ↓                           ↓
                                    #10 (单元测试)              #11 (集成测试)
                                          └─────────┬─────────────┘
                                                    ↓
                                              #12 (质量验收)
```

</details>

### M4: 工具目录 (第 13-16 周) — ✅ 已完成

> 交付物: tool-catalog 模块完成，10 个 RESTful 端点，工具审批流程 (draft → pending_review → approved/rejected → deprecated)
> 验收标准: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过
> 验收结果: **842 测试通过，覆盖率 94.65%（tool-catalog 97.91%），ruff/mypy 全通过，架构合规 14/14 通过**

<details>
<summary>展开查看 M4 任务详情</summary>

#### 领域模型设计摘要

**Tool 实体**: name, description, tool_type(ToolType), version, status(ToolStatus), creator_id, config(ToolConfig), reviewer_id, review_comment, reviewed_at, allowed_roles
**ToolStatus 枚举**: DRAFT → PENDING_REVIEW → APPROVED / REJECTED → DEPRECATED
**ToolType 枚举**: MCP_SERVER / API / FUNCTION
**ToolConfig 值对象**: server_url, transport, endpoint_url, method, headers, runtime, handler, code_uri, auth_type, auth_config（frozen dataclass, 扁平结构）

**状态机规则**:
- `submit()`: DRAFT → PENDING_REVIEW（需 name + description + config 完整）
- `approve(reviewer_id)`: PENDING_REVIEW → APPROVED
- `reject(reviewer_id, comment)`: PENDING_REVIEW → REJECTED
- `resubmit()`: REJECTED → PENDING_REVIEW（修改后重新提交）
- `deprecate()`: APPROVED → DEPRECATED（不可逆）
- 仅 DRAFT 状态可物理删除；DRAFT/REJECTED 可编辑

**API 端点**: POST /tools, GET /tools, GET /tools/approved, GET /tools/{id}, PUT /tools/{id}, DELETE /tools/{id}, POST /tools/{id}/submit, POST /tools/{id}/approve, POST /tools/{id}/reject, POST /tools/{id}/deprecate

**权限模型**: ADMIN 可审批/废弃所有工具；DEVELOPER 注册和管理自己的工具；approved 工具对所有认证用户可用

#### 任务拆解

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | tool-catalog/domain: Tool 实体 + ToolStatus/ToolType 枚举 + ToolConfig 值对象 + 状态机 (submit/approve/reject/resubmit/deprecate) | 已完成 | - | `rules/architecture.md` §5 DDD 战术模式 | 2026-02-09 |
| 2 | tool-catalog/domain: 领域事件 (Created/Updated/Deleted/Submitted/Approved/Rejected/Deprecated) + 模块异常 + IToolRepository 接口 | 已完成 | #1 | `rules/architecture.md` §4.2 事件驱动, §5.4 仓库接口 | 2026-02-09 |
| 3 | tool-catalog/application: DTO (CreateTool/UpdateTool/Tool/PagedTool) + ToolCatalogService (CRUD + 审批流程 + 列表/搜索 + 权限) | 已完成 | #1, #2 | `rules/architecture.md` §5 + `rules/security.md` §2 RBAC | 2026-02-09 |
| 4 | tool-catalog/infrastructure: ToolModel ORM + ToolRepositoryImpl (含 list_filtered 通用筛选) + Alembic migration | 已完成 | #2 | `rules/tech-stack.md` + `rules/project-structure.md` | 2026-02-09 |
| 5 | tool-catalog/api: Request/Response Schema + dependencies.py + endpoints.py (10 个端点含审批流程) | 已完成 | #3, #4 | `rules/api-design.md` + `rules/security.md` | 2026-02-09 |
| 6 | 模块注册: main.py 路由注册 + tool-catalog 异常映射 + __init__.py 模块导出 | 已完成 | #5 | `rules/architecture.md` §6.3 模块导出 | 2026-02-09 |
| 7 | tests: tool-catalog 模块单元测试 (Domain 状态机全路径 + Application Service 全场景含审批权限) | 已完成 | #1-#3 | `rules/testing.md` TDD + AAA 模式 | 2026-02-09 |
| 8 | tests: tool-catalog 模块集成测试 (Repository 含筛选 + API 端点含审批流程 + 架构合规更新) | 已完成 | #4-#6, #7 | `rules/testing.md` 集成测试 | 2026-02-09 |
| 9 | 质量验收: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过 | 已完成 | #1-#8 | `rules/checklist.md` + roadmap.md §3.6 | 2026-02-09 |

#### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| ToolConfig 存储 | ORM 展开为独立列 | 与 AgentConfig 模式一致；便于查询和索引 |
| 权限模型 | Tool.allowed_roles 字段 | YAGNI — Phase 2 简化；Phase 4 可升级为独立权限表 |
| REJECTED 状态 | 独立状态 + resubmit() | 审计追踪需要区分"从未审批"和"审批被拒" |
| 名称唯一性 | 同 creator 下唯一（联合索引） | 与 Agent owner_id+name 模式一致 |
| 删除策略 | 仅 DRAFT 可物理删除 | 进入审批流程的工具需保留记录 |
| Config 验证时机 | 提交审批时（submit/resubmit） | DRAFT 允许不完整；提交时强制校验 |
| 通用筛选 | Repository 提供 list_filtered | 支持 status+type+keyword 组合查询 |
| IToolQuerier 跨模块接口 | 延迟到 templates 模块开发时 | YAGNI — 当前无消费方 |

#### 依赖关系图

```
#1 (Domain 实体/值对象/状态机) ──► #2 (事件/异常/仓库接口) ──► #3 (Application)
                                                        └──► #4 (Infrastructure) ──► #5 (API) ──► #6 (模块注册)
#1-#3 ──► #7 (单元测试)
#4-#7 ──► #8 (集成测试)
#1-#8 ──► #9 (质量验收)
```

</details>

### M5: 知识库 (第 17-20 周) — ✅ 已完成

> 交付物: knowledge 模块完成 (知识库 CRUD + 文档上传 + RAG 检索集成)
> 验收标准: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过; Top-5 召回率 >= 80%
> 验收结果: **1023 测试通过，覆盖率 95.10%，ruff/mypy 全通过，架构合规 14/14 通过**
> 技术选型: MySQL (关系数据) + Bedrock Knowledge Bases (向量检索), 见 ADR-005

#### 领域模型设计摘要

**KnowledgeBase 实体**: name, description, status(KnowledgeBaseStatus), owner_id, agent_id(可选绑定), bedrock_kb_id(Bedrock KB 资源 ID), s3_prefix(文档存储路径)
**Document 实体**: knowledge_base_id, filename, s3_key, file_size, status(DocumentStatus), content_type, chunk_count
**KnowledgeBaseStatus 枚举**: CREATING → ACTIVE → SYNCING → FAILED → DELETED
**DocumentStatus 枚举**: UPLOADING → PROCESSING → INDEXED → FAILED

**核心流程**:
- 创建知识库: 创建 KnowledgeBase 记录 + 调用 Bedrock CreateKnowledgeBase API
- 上传文档: 上传到 S3 + 创建 Document 记录 + 触发 Bedrock StartIngestionJob
- RAG 检索: 调用 Bedrock Retrieve API (语义搜索) → 返回相关文档片段
- 与 Agent 集成: Agent 对话时自动检索关联知识库, 将结果作为上下文注入 LLM

**外部服务抽象**:
- `IKnowledgeService` → `BedrockKnowledgeAdapter` (Bedrock Knowledge Bases API 薄封装)
- `IDocumentStorage` → `S3DocumentStorage` (S3 上传/下载)

**API 端点**:
- `POST /knowledge-bases` — 创建知识库
- `GET /knowledge-bases` — 列表
- `GET /knowledge-bases/{id}` — 详情
- `PUT /knowledge-bases/{id}` — 更新
- `DELETE /knowledge-bases/{id}` — 删除
- `POST /knowledge-bases/{id}/documents` — 上传文档
- `GET /knowledge-bases/{id}/documents` — 文档列表
- `DELETE /knowledge-bases/{id}/documents/{doc_id}` — 删除文档
- `POST /knowledge-bases/{id}/sync` — 手动触发同步
- `POST /knowledge-bases/{id}/query` — RAG 检索

#### 任务拆解

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | knowledge/domain: KnowledgeBase 实体 + KnowledgeBaseStatus 枚举 + 状态机 (create/activate/sync/fail/delete) | 已完成 | - | `rules/architecture.md` §5 DDD 战术模式 | 2026-02-10 |
| 2 | knowledge/domain: Document 实体 + DocumentStatus 枚举 + 状态机 (upload/process/index/fail) | 已完成 | #1 | `rules/architecture.md` §5 | 2026-02-10 |
| 3 | knowledge/domain: 领域事件 (KBCreated/Activated/SyncStarted/DocUploaded/DocIndexed) + 模块异常 + IKnowledgeBaseRepository + IDocumentRepository | 已完成 | #1, #2 | `rules/architecture.md` §4.2, §5.4 | 2026-02-10 |
| 4 | knowledge/application: IKnowledgeService 接口 (createKB/deleteKB/startSync/retrieve) + IDocumentStorage 接口 (upload/delete/getUrl) | 已完成 | #1, #2 | `rules/architecture.md` §4.3 接口位置 | 2026-02-10 |
| 5 | knowledge/application: DTO (CreateKB/UpdateKB/KB/PagedKB/Document/UploadDoc/QueryRequest/QueryResult) + KnowledgeService (CRUD + 上传 + 同步 + 检索 + 权限) | 已完成 | #3, #4 | `rules/architecture.md` §5 + `rules/security.md` §2 | 2026-02-10 |
| 6 | knowledge/infrastructure/persistence: KnowledgeBaseModel + DocumentModel ORM + Repos 实现 + Alembic migration | 已完成 | #3 | `rules/tech-stack.md` + `rules/project-structure.md` | 2026-02-10 |
| 7 | knowledge/infrastructure/external: BedrockKnowledgeAdapter (boto3 bedrock-agent 薄封装 < 100 行) | 已完成 | #4 | `rules/sdk-first.md` 封装规则 + ADR-005 | 2026-02-10 |
| 8 | knowledge/infrastructure/external: S3DocumentStorage (boto3 s3 upload/delete/presigned_url) | 已完成 | #4 | `rules/sdk-first.md` | 2026-02-10 |
| 9 | knowledge/api: Request/Response Schema + dependencies.py + endpoints.py (10 端点) | 已完成 | #5, #6, #7, #8 | `rules/api-design.md` + `rules/security.md` | 2026-02-10 |
| 10 | 模块注册: main.py 路由注册 + knowledge 异常映射 + __init__.py 模块导出 | 已完成 | #9 | `rules/architecture.md` §6.3 | 2026-02-10 |
| 11 | execution 集成: send_message 中检测 Agent 关联的 KnowledgeBase, 自动调用 RAG 检索注入上下文 | 已完成 | #5, #7 | ADR-005 + `rules/architecture.md` §4.1 | 2026-02-10 |
| 12 | tests: knowledge 模块单元测试 (Domain 实体/状态机 + Application Service mock 外部服务) | 已完成 | #1-#5 | `rules/testing.md` TDD + AAA 模式 | 2026-02-10 |
| 13 | tests: knowledge 模块集成测试 (Repository + API 端点 + 架构合规更新) | 已完成 | #6-#10, #12 | `rules/testing.md` 集成测试 | 2026-02-10 |
| 14 | 质量验收: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过 | 已完成 | #1-#13 | `rules/checklist.md` + roadmap.md §3.6 | 2026-02-10 |

#### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 向量存储 | Bedrock Knowledge Bases (非 pgvector/OpenSearch) | ADR-005: 全托管零运维, 与现有 MySQL 无冲突, SDK-First |
| 文档存储 | S3 | product-architecture.md §6.2 数据存储策略 |
| KnowledgeBase 元数据 | MySQL | 关系数据, 与其他模块一致 |
| 与 Agent 绑定 | agent_id 可选字段 | 一个 KB 可被多个 Agent 引用; 对话时按 Agent 关联 KB 检索 |
| RAG 注入时机 | send_message 前自动检索 | 透明集成, 用户无需手动调用检索 API |
| 文档同步 | 异步 (Bedrock IngestionJob) | 文档处理耗时, 不阻塞用户操作 |
| 跨模块通信 | shared/interfaces/IKnowledgeQuerier | 遵循模块隔离 R1/R3, execution 不直接依赖 knowledge |

#### 依赖关系图

```
#1 (KB 实体) ──► #2 (Document 实体) ──► #3 (事件/异常/仓库接口) ──► #5 (Application)
                                                            └──► #6 (ORM + 迁移)
#4 (外部服务接口) ──► #5 (KnowledgeService)
                  ├──► #7 (Bedrock 适配器)
                  └──► #8 (S3 适配器)
#5-#8 ──► #9 (API 端点) ──► #10 (模块注册)
#5, #7 ──► #11 (execution 集成)
#1-#5 ──► #12 (单元测试)
#6-#12 ──► #13 (集成测试)
#1-#13 ──► #14 (质量验收)
```

### M7: Multi-Agent 编排 (第 29-36 周) — ✅ 已完成

> 交付物: Agent Teams 能力 (ADR-008: 替代 DAG 引擎) + 生产化加固 + insights 集成
> 验收标准: ruff check + mypy + pytest --cov-fail-under=85 全通过；用户可提交团队执行任务并追踪进度
> 技术决策: ADR-008 — Agent Teams 替代 DAG 引擎，在 execution 模块内扩展

#### 领域模型设计摘要

**TeamExecution 实体**: agent_id, user_id, conversation_id(可选), prompt, status(TeamExecutionStatus), result, error_message, input_tokens, output_tokens, started_at, completed_at
**TeamExecutionLog 实体**: execution_id, sequence, log_type, content
**TeamExecutionStatus 枚举**: PENDING → RUNNING → COMPLETED / FAILED / CANCELLED

**核心流程**:
- 提交团队执行: 校验 Agent ACTIVE + enable_teams → 创建 TeamExecution(PENDING) → 启动 asyncio.Task 后台执行
- 后台执行: asyncio.Semaphore(3) 并发控制 → 注入 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` → 流式消费 SDK → 记录进度日志 → 完成/失败
- SSE 进度推送: 轮询日志表 yield 增量日志
- 取消执行: PENDING/RUNNING → CANCELLED, 取消 asyncio.Task

**AgentConfig 扩展**: `enable_teams: bool = False` 开关字段
**ClaudeAgentAdapter**: 团队模式注入环境变量 + 自动提升 max_turns=200

**API 端点**: POST /team-executions, GET /team-executions, GET /team-executions/{id}, GET /team-executions/{id}/logs, GET /team-executions/{id}/stream, POST /team-executions/{id}/cancel

#### 任务拆解

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | AgentConfig 扩展 enable_teams + 全链路传递 (constants/DTO/Schema/Response/ORM/Querier) | 已完成 | - | `rules/architecture.md` §5 | 2026-02-12 |
| 2 | ClaudeAgentAdapter Teams 支持 (env 注入 + max_turns 提升) | 已完成 | #1 | ADR-008 + `rules/sdk-first.md` | 2026-02-12 |
| 3 | TeamExecution 领域模型 (实体 + 状态机 + 日志 + 仓库接口 + 事件 + 异常) | 已完成 | - | `rules/architecture.md` §5 DDD 战术模式 | 2026-02-12 |
| 4 | TeamExecution ORM + Alembic 迁移 (enable_teams 列 + team_executions + team_execution_logs 表) | 已完成 | #3 | `rules/tech-stack.md` | 2026-02-12 |
| 5 | TeamExecutionService (submit/get/list/cancel/stream_logs + asyncio.Task 后台执行) | 已完成 | #2, #3, #4 | `rules/architecture.md` §5 + ADR-008 | 2026-02-12 |
| 6 | API 层 (6 端点 + SSE + dependencies + main.py 注册) | 已完成 | #5 | `rules/api-design.md` | 2026-02-12 |
| 7 | Settings 扩展 (TEAM_EXECUTION_MAX_TURNS/TIMEOUT/MAX_CONCURRENT) | 已完成 | #5 | `rules/tech-stack.md` | 2026-02-12 |
| 8 | 测试 (79 个: 领域 + 应用 + 基础设施 + 既有测试适配) | 已完成 | #1-#7 | `rules/testing.md` TDD | 2026-02-12 |
| 9 | ADR-008 创建 (Agent Teams 替代 DAG 引擎决策记录) | 已完成 | - | `rules/architecture.md` §2 ADR 触发 | 2026-02-12 |
| 10 | 端到端验证 (部署迁移 + 创建 Teams Agent + 提交执行) | 已完成 | #1-#9 | - | 2026-02-12 |
| 11 | 生产化加固 (重试机制 + Token 预算控制 + 错误分类) | 已完成 | #10 | ADR-008 | 2026-02-12 |
| 12 | insights 集成 (团队执行的成本归因) | 已完成 | #10 | - | 2026-02-12 |
| 13 | 质量验收: ruff check + mypy + pytest 全通过 | 已完成 | #10-#12 | `rules/checklist.md` | 2026-02-12 |

#### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 编排策略 | Agent Teams (非 DAG 引擎) | ADR-008: 复杂度低、灵活性高、SDK 杠杆、前端轻量 |
| 配置方式 | `enable_teams` 布尔字段 | Teams 是 Agent 能力增强，非独立运行时 |
| 数据模型 | 新增 TeamExecution (非扩展 Conversation) | 长任务 vs 多轮对话语义不同 |
| 后台引擎 | asyncio.Task (MVP) | 无额外依赖；后续可升级 Celery/SQS |
| 并发控制 | asyncio.Semaphore(3) | 防止资源耗尽 |
| Token 控制 | max_turns=200 间接控制 | SDK 暂不支持 max_budget 直接参数 |

### M10-prep: 执行层分离 + 技术基线升级 (第 53-56 周) — ✅ 已完成

> 交付物: P3-4/P3-5 执行层部署分离 + SDK/CDK/Aurora 升级 + OTEL 修复
> 验收标准: AgentCore Runtime 健康检查通过；双执行路径可切换；14 个被阻断集成测试恢复；infra 快照通过
> 验收结果: **1673 后端测试 + 161 infra 测试全通过；AgentCoreRuntimeAdapter 实现 + AGENT_RUNTIME_MODE 配置切换；SDK MCP Server 正式集成**
> 来源: Phase 4 季度评审 (v1.5, 2026-02-13) — 四维度评审产出

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | SDK 包名更新 (`claude-agent-sdk`) + CDK agentcore alpha 升级 (BREAKING CHANGE 适配) | 已完成 | - | `agentcore-integration-plan.md` | 2026-02-13 |
| 2 | Aurora MySQL 3.10.0 → 3.10.3 升级 (Dev 验证 → Prod 跟随) | 已完成 | - | `rules/tech-stack.md` | 2026-02-13 |
| 3 | OTEL instrumentation-sqlalchemy 安装问题修复 (解除 14 个集成测试阻断) | 已完成 | - | `rules/testing.md` | 2026-02-13 |
| 4 | C-P3-4: Agent 容器镜像构建 + ECR 推送 + Runtime 部署验证 | 已完成 | #1 | `agentcore-integration-plan.md` §5 P3-4 | 2026-02-13 |
| 5 | C-P3-5: AgentCoreRuntimeAdapter 实现 + 调用路径切换 (配置可切换, 保留降级) | 已完成 | #4 | `agentcore-integration-plan.md` §5 P3-5 | 2026-02-13 |
| 6 | infra 快照测试全量更新 + worker 进程泄漏修复 | 已完成 | #1 | `rules/testing.md` | 2026-02-13 |
| 7 | ClaudeAgentAdapter 2 个 TODO 清理 | 已完成 | #5 | `rules/architecture.md` | 2026-02-13 |
| 8 | CI/CD Pipeline 补充 Agent 镜像构建推送流程 | 已完成 | #4 | `.github/workflows/` | 2026-02-13 |
| 9 | 质量验收: ruff + mypy + pytest 全通过 + Runtime E2E 验证 | 已完成 | #1-#8 | `rules/checklist.md` | 2026-02-13 |

### M10: 审计合规 + 前端补全 (第 57-64 周) — ✅ 已完成

> 交付物: audit 模块 (10 任务) + 前端 5 页面补全 (7 任务)；覆盖度 45% → 85%
> 验收标准: 100% 写操作审计覆盖 + 前端 13+ 页面 + ruff/mypy/pytest 全通过
> 来源: roadmap v1.5 §5.5 + v1.6 季度评审 M10 任务拆解

#### 后端 audit 模块 (10 任务) — ✅ 全部完成

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | audit/domain: AuditLog 实体 + AuditAction/AuditCategory 枚举 + IAuditLogRepository 接口 | 已完成 | - | `rules/architecture.md` §5 DDD | 2026-02-13 |
| 2 | audit/domain: 领域事件 (AuditLogCreated) + 模块异常 | 已完成 | #1 | `rules/architecture.md` §4.2 | 2026-02-13 |
| 3 | audit/application: DTO + AuditService (记录/查询/统计/按资源查询) | 已完成 | #1, #2 | `rules/architecture.md` §5 | 2026-02-13 |
| 4 | audit/application: IAuditEventSubscriber 接口 (订阅各模块 DomainEvent 自动记录审计) | 已完成 | #3 | `rules/architecture.md` §4.2 EventBus | 2026-02-13 |
| 5 | audit/infrastructure: AuditLogModel ORM + AuditLogRepositoryImpl + Alembic migration | 已完成 | #1 | `rules/tech-stack.md` | 2026-02-13 |
| 6 | audit/infrastructure: AuditEventSubscriber 实现 (EventBus 订阅 → AuditLog 记录, 23 事件) | 已完成 | #4, #5 | `rules/architecture.md` §4.2 | 2026-02-13 |
| 7 | audit/api: Schema + dependencies + endpoints (列表/筛选/统计/按资源/导出 CSV) — 仅 ADMIN | 已完成 | #3, #5 | `rules/api-design.md` | 2026-02-13 |
| 8 | 审计中间件: AuditMiddleware (自动记录 API 调用 — method/path/status/actor/duration) | 已完成 | #3 | `rules/observability.md` | 2026-02-13 |
| 9 | 模块注册: main.py 路由 + 异常映射 + EventBus 订阅注册 | 已完成 | #6, #7, #8 | `rules/architecture.md` §6.3 | 2026-02-13 |
| 10 | tests: audit 单元测试 + 集成测试 + 质量验收 (65 测试) | 已完成 | #1-#9 | `rules/testing.md` TDD | 2026-02-13 |

#### 前端 5 页面补全 (7 任务) — ✅ 全部完成

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 11 | KnowledgePage — 知识库管理 (10 文件, 对接 10 端点) | 已完成 | - | FSD 架构 | 2026-02-13 |
| 12 | TemplatesPage — 模板管理 (10 文件, 对接 8 端点) | 已完成 | - | FSD 架构 | 2026-02-13 |
| 13 | ToolCatalogPage — 工具目录 (9 文件, 对接 10 端点) | 已完成 | - | FSD 架构 | 2026-02-13 |
| 14 | InsightsPage — 使用洞察 (7 文件, 对接 3 端点, recharts 图表) | 已完成 | - | FSD 架构 | 2026-02-13 |
| 15 | EvaluationPage — 评估管理 (12 文件, 对接 14 端点) | 已完成 | - | FSD 架构 | 2026-02-13 |
| 16 | 前端路由整合 + 导航更新 (Sidebar 分组导航 9 项 + 5 图标 + 懒加载) | 已完成 | #11-#15 | - | 2026-02-13 |
| 17 | 前端测试 + 覆盖度验证 (19 文件 90 测试全通过, 176 源文件, 12 页面目录) | 已完成 | #16 | - | 2026-02-13 |

#### M10 并行策略

```
后端 audit (#1-#10) 与前端 (#11-#15) 100% 并行，无交叉依赖
前端 5 页面 (#11-#15) 互相独立，可并行开发
```

### M11: 平台成熟化 (第 65-70 周)

> 交付物: insights 修复 (前后端 API 对齐 + 数据采集修复) + 灾备验证 + Agent 体验优化 + Opus 4.6 评估
> 验收标准: insights 前端 3 个图表全部有真实数据；普通对话和团队执行均记录成本；灾备演练方案可执行；ruff + mypy + pytest 全通过
> 关键发现: M10 构建的 InsightsPage 前端调用 `cost-breakdown` 和 `usage-trends` 两个后端不存在的端点；model_id 硬编码；普通对话不记录成本

#### A. Insights 数据采集修复（优先级最高）

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | 修复 model_id 硬编码 + CostExplorerAdapter + 订阅 MessageReceivedEvent + estimated_cost 弃用 (改用 AWS Cost Explorer 真实账单) | 已完成 | - | `rules/architecture.md` §4.2 EventBus | 2026-02-13 |
| 2 | ~~BedrockCostCalculator 定价表扩展~~ — 已弃用: 平台总成本依托 AWS Cost Explorer, estimated_cost 固定为 0.0 | 已完成 | - | `rules/sdk-first.md` | 2026-02-13 |

#### B. Insights 后端 API 补全（修复 M10 前后端 gap）

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 3 | InsightsService 新增 `get_cost_breakdown()` + `get_usage_trends()` + `get_insights_summary()`; Repository 新增 3 个聚合查询 | 已完成 | #1 | `rules/architecture.md` §5 DDD | 2026-02-13 |
| 4 | insights API 新增 2 端点 (`GET /cost-breakdown`, `GET /usage-trends`) + 增强 `GET /summary` (total_agents/active_agents/total_tokens/total_cost from CE) | 已完成 | #3 | `rules/api-design.md` | 2026-02-13 |
| 5 | Insights 后端测试 (22 个新测试: CostExplorerAdapter 3 + InsightsService 增强 8 + 集成测试 11), 全模块 96 测试通过 | 已完成 | #1-#4 | `rules/testing.md` TDD | 2026-02-13 |

#### C. Insights 前端联调

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 6 | 前端 types/CostBreakdownChart/InsightsSummary/UsageTrendChart 全部对齐: cost→tokens, 移除 avg_response_time_ms, 新增 total_tokens 卡片 | 已完成 | #4 | FSD 架构 | 2026-02-13 |

#### D. 灾备验证

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 7 | CDK 增强: Prod Performance Insights + KnowledgeDocsBucket (S3 版本管理) + infra 179 测试 | 已完成 | - | infra 规范 | 2026-02-13 |
| 8 | 灾备演练方案 (RPO<5min/RTO<15min) + Aurora 快照恢复脚本 + S3 版本回滚脚本 | 已完成 | #7 | roadmap.md §5.4 | 2026-02-13 |
| 9 | C-S4-8: Dev 环境非工作时段定时缩减 (ECS Scheduled Scaling, UTC 12:00 缩减到 0, UTC 00:00 恢复到 1) | 已完成 | - | roadmap.md §5.4 成本优化 | 2026-02-13 |

#### E. Agent 体验优化

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 10 | 后端: Agent 预览端点 (`POST /agents/{id}/preview`) — execution 模块实现, max_turns=1, 不创建 Conversation | 已完成 | - | `rules/architecture.md` §4.4 | 2026-02-13 |
| 11 | 前端: Prompt Editor 增强 (字符计数 + 模型成本对比 + temperature 说明) + AgentDetailPage 测试面板 | 已完成 | #10 | FSD 架构 | 2026-02-13 |

#### F. Opus 4.6 评估 + 质量验收

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 12 | ADR-010: Opus 4.6 模型集成评估 — 维持 Haiku 默认 + 模型选择指南 (简单→Haiku/代码→Sonnet/推理→Opus) | 已完成 | #2 | ADR 流程 | 2026-02-13 |
| 13 | M11 质量验收: ruff ✅ mypy ✅ 1826 后端测试 ✅ 179 infra 测试 ✅ 前端 TS ✅ 架构合规 14/14 ✅ | 已完成 | #1-#12 | `rules/checklist.md` | 2026-02-13 |

#### M11 并行策略

```
主线: A 数据采集修复 (#1-#2) ──► B 后端 API 补全 (#3-#5) ──► C 前端联调 (#6)
并行: D 灾备验证 (#7-#9)        与主线 100% 并行，无交叉依赖
并行: E Agent 体验优化 (#10-#11) 与主线 100% 并行，无交叉依赖
并行: F Opus 评估 (#12)          依赖 #2 (定价表)，可与 B/D/E 并行
```

### M12: 全公司推广 + AgentCore 深度集成 (第 71-76 周)

> 交付物: AgentCore Identity/Memory/A2A 深度集成 + API 文档+用户手册 + 性能压测 + 梯度推广 50+ 用户
> 验收标准: roadmap §5.6 全部达标; >= 50 活跃用户; >= 40% 非技术自助创建; P95 < 300ms (非 LLM); 积压清零
> 来源: M12 规划拆解 (2026-02-14)

#### 阶段一：ADR 战略决策 (Week 1) — 3 任务并行

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 1 | C-S3-4: A2A 协议采纳评估 → `docs/adr/011-a2a-protocol-evaluation.md` | 已完成 | - | ADR 流程 | 2026-02-14 |
| 2 | C-S3-5: 蓝绿部署评估 → `docs/adr/012-blue-green-deployment.md` | 已完成 | - | ADR 流程 | 2026-02-14 |
| 3 | C-S3-6: Strands vs claude-agent-sdk 评估 → `docs/adr/013-strands-evaluation.md` | 已完成 | - | ADR 流程 + ADR-006 | 2026-02-14 |

#### 阶段二：AgentCore 深度集成 (Week 1-4) — 3 工作流

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 4 | C-P3-3: Identity OAuth 2.0 Provider + Gateway 入站认证 | 已完成 | - | `agentcore-integration-plan.md` §5 P3-3 | 2026-02-14 |
| 5 | C-P3-3: Token Vault 第三方 API Key 管理 | 已完成 | #4 | `agentcore-integration-plan.md` §5 P3-3 | 2026-02-14 |
| 6 | C-P3-1: Memory Strategy 配置 + 异步记忆提取 | 已完成 | - | `agentcore-integration-plan.md` §5 P3-1 | 2026-02-14 |
| 7 | C-P3-1: Agent 执行自动上下文注入 (长期记忆) | 已完成 | #6 | `agentcore-integration-plan.md` §5 P3-1 | 2026-02-14 |
| 8 | C-P3-2: A2A 跨 Runtime Agent 通信 | 已完成 | #1 | `agentcore-integration-plan.md` §5 P3-2 | 2026-02-14 |

#### 阶段三：文档 + 压测 (Week 2-5) — 与代码 100% 并行

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 9 | C-S4-9: API 文档 + 用户手册 + 快速入门 | 已完成 | - | `rules/api-design.md` | 2026-02-14 |
| 10 | 性能压测 (locust) + 50 并发验证 | 已完成 | - | roadmap §5.6 P95 < 300ms | 2026-02-14 |
| 11 | 培训材料 + Onboarding 流程 | 已完成 | #9 | - | 2026-02-14 |

#### 阶段四：梯度推广 (Week 4-6)

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 12 | 梯度推广 10→30→50 + 反馈模板 | 已完成 | #9, #10, #11 | roadmap §5.6 | 2026-02-14 |

#### 阶段五：收尾 (Week 5-6)

| # | 任务 | 状态 | 依赖 | 参考规范 | 会话 |
|---|------|:----:|:----:|---------|------|
| 13 | 遗留事项清理 (#6 Sonnet + #14 Docker) | 已完成 | - | - | 2026-02-14 |
| 14 | M12 + Phase 4 质量验收 | 已完成 | #1-#13 | `rules/checklist.md` + roadmap §5.6 | 2026-02-14 |

#### M12 并行策略

```
Session 1:  #1 + #2 + #3 (3 ADR 并行)
Session 2:  #4 + #6 + #9 + #10 (Identity + Memory + 文档 + 压测，4 路并行)
Session 3:  #5 + #7 + #8 + #11 (Token Vault + 记忆注入 + A2A + 培训)
Session 4:  #12 (推广) + #13 (遗留清理)
Session 5:  #14 (质量验收) + progress.md 更新
```

---

## 变更积压 (Change Backlog)

> **来源**: `docs/strategy/improvement-plan.md` 五维度深度审查
> **注入日期**: 2026-02-10
> **S5 不入积压表**，保留在 improvement-plan.md 按季度评审

### 执行规则

1. **S0 阻断优先**: 有未完成 S0 时，必须优先完成，不得开始 M5 任务
2. **S1/S2 穿插执行**: 每 2-3 个 Milestone 任务后，穿插 1 个 S1 或 S2 变更
3. **S3 阻塞决策**: S3 不自动触发，需用户主动发起；但当 Milestone 任务依赖某 S3 决策时需提醒
4. **S4/S5 技术债务窗口**: Phase 结束时集中处理，或在相关模块开发时顺带修复

### S0 — 阻断修复（进入 M5 之前）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S0-1 | SSE 流式 session 生命周期修复 | 已完成 | - | 架构审查 A1 (P0) | execution 模块 | `improvement-plan.md` §2 S0-1 | 2026-02-10 |
| C-S0-2 | Alembic 迁移 ID 冲突修复 | 已完成 | - | 架构审查 A2 (P0) | migrations/ | `improvement-plan.md` §2 S0-2 | 2026-02-10 |
| C-S0-3 | Dockerfile + docker-compose 创建 | 已完成 | C-S0-2 | DevOps 审查 D7 (阻塞级) | 项目根目录 | `improvement-plan.md` §2 S0-3 | 2026-02-10 |
| C-S0-4 | MySQL 集成测试添加 | 已完成 | C-S0-3 | DevOps 审查 D2 (阻塞级) | tests/ + CI | `improvement-plan.md` §2 S0-4 | 2026-02-10 |
| C-S0-5 | `get_current_user` 添加 `is_active` 检查 | 已完成 | - | 安全审查 SEC11 (中危) | auth 模块 | `improvement-plan.md` §2 S0-5 | 2026-02-10 |
| C-S0-6 | JWT Secret 启动校验 | 已完成 | - | 安全审查 SEC1 (高危) | shared/settings | `improvement-plan.md` §2 S0-6 | 2026-02-10 |

### S1 — 安全加固（M5 开发期间并行）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S1-1 | 登录 Rate Limiting + 账户锁定 | 已完成 | - | 安全审查 SEC4+SEC5 (高危) | auth + 中间件 | `improvement-plan.md` §3 S1-1 | 2026-02-11 |
| C-S1-2 | Refresh Token 机制 | 已完成 | - | 安全审查 SEC2+SEC3 (高危) | auth 模块 | `improvement-plan.md` §3 S1-2 | 2026-02-11 |
| C-S1-3 | 基础安全审计日志 | 已完成 | - | 安全审查 SEC7 (高危) | auth + shared | `improvement-plan.md` §3 S1-3 | 2026-02-11 |
| C-S1-4 | 注册端点权限保护 | 已完成 | - | 安全审查 SEC16 (中危) | auth API | `improvement-plan.md` §3 S1-4 | 2026-02-11 |
| C-S1-5 | CORS 运行时校验 | 已完成 | C-S0-6 | 安全审查 SEC17 (中危) | shared/settings | `improvement-plan.md` §3 S1-5 | 2026-02-10 |

### S2 — 性能解锁（M5 开发期间并行）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S2-1 | 自定义线程池 + 连接池调优 | 已完成 | C-S0-1 | 性能审查 PERF1+PERF3 (HIGH) | shared/database + execution | `improvement-plan.md` §4 S2-1 | 2026-02-11 |
| C-S2-2 | 对话历史滑动窗口 | 已完成 | - | 性能审查 PERF4 (CRITICAL) | execution 模块 | `improvement-plan.md` §4 S2-2 | 2026-02-11 |
| C-S2-3 | EventBus 内存泄漏修复 | 已完成 | - | 性能审查 PERF9 + 架构审查 A3 | shared/event_bus | `improvement-plan.md` §4 S2-3 | 2026-02-10 |
| C-S2-4 | Agent 配置本地缓存 | 已完成 | - | 性能审查 PERF8 (HIGH) | agents 模块 | `improvement-plan.md` §4 S2-4 | 2026-02-11 |

### S3 — 战略决策（M5 启动前）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S3-1 | MySQL vs PostgreSQL 技术选型 (ADR) | 已完成 | - | DevOps D4 + 性能 PERF10 | 全项目数据库 | `improvement-plan.md` §5 S3-1 | 2026-02-10 |
| C-S3-2 | 端到端集成验证 (M4.5) | 已完成 | C-S0-3 | 产品审查 P2 | 前后端联调 | `improvement-plan.md` §5 S3-2 | 2026-02-11 |
| C-S3-3 | 路线图调整评审 | 已完成 | C-S3-1 | 产品审查 P1+P3+P10 | roadmap.md | `improvement-plan.md` §5 S3-3 | 2026-02-11 |

### S4 — 中期改进（Phase 2 完成前）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S4-1 | CI/CD Pipeline 完善 | 已完成 | C-S0-3, C-S0-4 | DevOps 审查 D3 | .github/workflows/ | `improvement-plan.md` §6 S4-1 | 2026-02-11 |
| C-S4-2 | CDK 首次部署验证 | 已完成 | C-S0-3 | DevOps 审查 D1 (阻塞级) | infra/ | `improvement-plan.md` §6 S4-2 | 2026-02-11 |
| C-S4-3 | Secrets 管理统一 | 已完成 | C-S0-6 | DevOps 审查 D6 | shared/settings + infra | `improvement-plan.md` §6 S4-3 | 2026-02-11 |
| C-S4-4 | 基础监控告警 | 已完成 | C-S4-2 | DevOps 审查 D8 | infra/ CDK | `improvement-plan.md` §6 S4-4 | 2026-02-11 |
| C-S4-5 | python-jose 迁移到 PyJWT | 已完成 | - | 安全审查 SEC19 | auth 模块 | `improvement-plan.md` §6 S4-5 | 2026-02-11 |
| C-S4-6 | 硬编码配置集中管理 (消除魔术数字 DRY 违规) | 已完成 | - | 代码审查 (2026-02-11) | agents + execution + templates + knowledge + shared | 见下方详细说明 | 2026-02-11 |

#### C-S4-6 详细说明

**问题**: 多个配置默认值以魔术数字形式散落在代码各层，违反 DRY 原则，修改时需同步多处。

**影响范围** (按严重程度排列):

| 配置值 | 重复次数 | 散布位置 | 风险 |
|--------|:--------:|---------|------|
| `max_tokens = 2048` | 9 处 | agents (Domain/DTO/Schema/ORM) + execution (接口/适配器) | 改默认值需改 9 个文件 |
| `max_tokens = 4096` | 4 处 | templates (Domain/DTO/Schema/ORM) | 与 agents 默认值不同，需确认是否有意为之 |
| `30000` / `2000` | 各 2 处 | settings.py (已定义) + execution_service.py (未引用 Settings) | Settings 配置项形同虚设 |
| `1800` | 2 处 | settings.py (DB_POOL_RECYCLE) + database.py (参数默认值) | 环境变量覆盖可能不生效 |
| `3600` | 3 处 | event_bus.py + document_storage 接口/实现 | 不同业务含义用同一数字，无命名常量 |
| `max_length=1000/2000/10000` | 10+ 处 | Domain 实体 Field + ORM String 列 | 两层各自硬编码，需人工保持一致 |

**建议修复方案**:
1. 在 `shared/domain/constants.py` 定义业务常量 (如 `DEFAULT_MAX_TOKENS`, `FIELD_LENGTH_*`)
2. 让 Domain/DTO/Schema/ORM 统一引用常量，而非各写魔术数字
3. `execution_service.py` 的构造函数应从 Settings 读取 `MAX_CONTEXT_TOKENS` / `SYSTEM_PROMPT_TOKEN_BUDGET`
4. `database.py` 的 `pool_recycle` 应从 Settings 读取 `DB_POOL_RECYCLE`

### 变更统计

| 级别 | 数量 | 时间窗口 | 当前进度 |
|------|:----:|---------|---------|
| S0 阻断修复 | 6 | 进入 M5 之前 | **6/6 ✅** |
| S1 安全加固 | 5 | M5 开发期间并行 | **5/5 ✅** |
| S2 性能解锁 | 4 | M5 开发期间并行 | **4/4 ✅** |
| S3 战略决策 | 3 | M5 启动前决策 | **3/3 ✅** |
| S4 中期改进 | 6 | Phase 2 完成前 | **6/6 ✅** |
| **合计** | **24** | - | **24/24 ✅** |

### AgentCore 集成积压 (来源: ADR-006 + agentcore-integration-plan.md)

> **注入日期**: 2026-02-10 | **来源**: 技术选型审查 + ADR-006

| 编号 | 行动项 | 状态 | 依赖 | 影响范围 | 参考规范 | 会话 |
|------|--------|:----:|:----:|---------|---------|------|
| C-P0-1 | 升级 boto3 + 引入 claude-agent-sdk / bedrock-agentcore 依赖 | 已完成 | - | pyproject.toml + tech-stack.md | `agentcore-integration-plan.md` §2 P0-1 | 2026-02-10 |
| C-P0-2 | 定义 IAgentRuntime 接口 (Agent Loop 抽象) | 已完成 | C-P0-1 | execution 模块 | `agentcore-integration-plan.md` §2 P0-2 | 2026-02-10 |
| C-P0-3 | 定义 IToolQuerier 跨模块接口 + ToolQuerierImpl | 已完成 | - | shared + tool_catalog | `agentcore-integration-plan.md` §2 P0-3 | 2026-02-10 |
| C-P0-4 | AgentConfig 新增 runtime_type 字段 + migration | 已完成 | - | agents 模块 | `agentcore-integration-plan.md` §2 P0-4 | 2026-02-10 |
| C-P0-5 | 落实可观测性基础 (structlog 配置 + Correlation ID + readiness) | 已完成 | - | shared + presentation | `agentcore-integration-plan.md` §2 P0-5 | 2026-02-10 |
| C-P0-6 | 完善 Bedrock KB 创建参数 + RAG 注入优化 | 已完成 | - | knowledge + execution | `agentcore-integration-plan.md` §2 P0-6 | 2026-02-10 |
| C-P1-1 | 实现 ClaudeAgentAdapter | 已完成 | C-P0-1~3 | execution 模块 | `agentcore-integration-plan.md` §3 P1-1 | 2026-02-10 |
| C-P1-2 | 扩展 ExecutionService 支持 IAgentRuntime | 已完成 | C-P0-2~4, C-P1-1 | execution 模块 | `agentcore-integration-plan.md` §3 P1-2 | 2026-02-10 |
| C-P1-3 | AgentCore Runtime CDK 资源 | 已完成 | C-P1-1 | infra/ | `agentcore-integration-plan.md` §3 P1-3 | 2026-02-10 |
| C-P1-4 | Agent 应用入口点 (BedrockAgentCoreApp + Claude Agent SDK) | 已完成 | C-P1-1, C-P1-3 | backend/agent_entrypoint | `agentcore-integration-plan.md` §3 P1-4 | 2026-02-10 |

> P2 行动项在 M7-prep 中完成。P3 行动项详见 `agentcore-integration-plan.md` §5，Phase 3-4 执行。

| 编号 | 行动项 | 状态 | 依赖 | 影响范围 | 参考规范 | 会话 |
|------|--------|:----:|:----:|---------|---------|------|
| C-P2-1 | AgentCore Gateway 工具同步集成 | 已完成 | C-P1-1 | tool_catalog + execution | `agentcore-integration-plan.md` §4 P2-1 | 2026-02-11 |
| C-P2-2 | AgentCore Memory MCP 桥接 | 已完成 | C-P1-2 | execution 模块 | `agentcore-integration-plan.md` §4 P2-2 | 2026-02-11 |
| C-P2-3 | OpenTelemetry / AgentCore Observability | 已完成 | C-P0-5 | shared + execution + knowledge | `agentcore-integration-plan.md` §4 P2-3 | 2026-02-11 |

> P3 行动项。注: C-P3-4/P3-5 为 Agent 容器部署和调用路径切换——当前 Platform API 通过 ClaudeAgentAdapter 在 ECS Fargate 进程内直接调用 claude_agent_sdk.query()，尚未经由 AgentCore Runtime 执行。agent_entrypoint.py + Dockerfile.agent + AgentCoreStack CDK 已就绪（P1-3/P1-4），但缺少容器构建推送和调用路径切换。

| 编号 | 行动项 | 状态 | 依赖 | 影响范围 | 参考规范 | 会话 |
|------|--------|:----:|:----:|---------|---------|------|
| C-P3-1 | AgentCore Memory 长期记忆策略 | 已完成 | C-P2-2 | execution 模块 | `agentcore-integration-plan.md` §5 P3-1 | 2026-02-14 |
| C-P3-2 | 多 Agent 编排 (AgentCore Runtime A2A) | 已完成 | C-P1-1, C-P1-2 | execution 模块 | `agentcore-integration-plan.md` §5 P3-2 | 2026-02-14 |
| C-P3-3 | AgentCore Identity 集成 | 已完成 | C-P2-1 | auth + gateway | `agentcore-integration-plan.md` §5 P3-3 | 2026-02-14 |
| C-P3-4 | Agent 容器镜像构建 + ECR 推送 + AgentCore Runtime 部署验证 | 已完成 | C-P1-3, C-P1-4 | Dockerfile.agent + CI/CD + infra | `agentcore-integration-plan.md` §5 P3-4 | 2026-02-13 |
| C-P3-5 | Platform API → AgentCore Runtime 调用路径切换 | 已完成 | C-P3-4 | execution 模块 (AgentCoreRuntimeAdapter 新增) | `agentcore-integration-plan.md` §5 P3-5 | 2026-02-13 |

| 级别 | 数量 | 时间窗口 | 当前进度 |
|------|:----:|---------|---------|
| P0 基础就绪 | 6 | M6 之前 | **6/6 ✅** |
| P1 核心集成 | 4 | M6 期间 | **4/4 ✅** |
| P2 平台能力 | 3 | M7-prep | **3/3 ✅** |
| P3 深度集成 | 5 | M10-prep + M12 | **5/5 ✅** |
| **合计** | **18** | - | **18/18 ✅** |

### Phase 4 变更积压 (来源: Phase 4 季度评审 v1.5)

> **注入日期**: 2026-02-13 | **来源**: 四维度评审 (代码审计 + 外部技术变化 + Phase 3 经验教训 + 路线图拆解)

#### S0 — 阻断修复（M10-prep 之前）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S0-7 | SDK 包名更新 `claude-agent-sdk` (BREAKING) | 已完成 | - | 外部技术变化 | pyproject.toml + imports | `agentcore-integration-plan.md` | 2026-02-13 |
| C-S0-8 | CDK agentcore alpha BREAKING CHANGE 适配 (User Pool Client 替换) | 已完成 | - | 外部技术变化 | infra/ AgentCoreStack | CDK 变更日志 | 2026-02-13 |
| C-S0-9 | OTEL instrumentation-sqlalchemy 安装修复 (14 个集成测试被阻断) | 已完成 | - | 代码审计 | 测试基础设施 | `rules/testing.md` | 2026-02-13 |
| C-S0-10 | bedrock-agentcore 升级 0.x→1.x + API 兼容性验证 | 已完成 | - | v1.6 外部技术扫描 | pyproject.toml + adapter 代码 | - | 2026-02-13 |

#### S1 — 安全与稳定（M10 期间并行）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S1-6 | Aurora MySQL 3.10.0 → 3.10.3 安全更新 | 已完成 | - | 外部技术变化 | infra/ DatabaseStack | CDK + Aurora 文档 | 2026-02-13 |
| C-S1-7 | infra 快照测试全量更新 (当前过期) | 已完成 | C-S0-8 | 代码审计 | infra/test/ | `rules/testing.md` | 2026-02-13 |
| C-S1-8 | infra worker 进程泄漏修复 | 已完成 | - | 代码审计 | infra/ 测试 | - | 2026-02-13 |
| C-S1-9 | Ruff ANN101 配置忽略 + 自动修复 4 项 (RUF100/I001) | 已完成 | - | v1.6 代码审计 | pyproject.toml + src/ | - | 2026-02-13 |
| C-S1-10 | MyPy execution 模块 8 个新增类型错误修复 (bg_repo_factory 类型签名) | 已完成 | - | v1.6 代码审计 | execution 模块 | - | 2026-02-13 |

#### S2 — 技术债务（M10-M11 穿插）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S2-5 | ClaudeAgentAdapter 2 个 TODO 清理 (MCP Server 封装) | 已完成 | C-S0-7 | 代码审计 | execution 模块 | - | 2026-02-13 |
| C-S2-6 | 前端覆盖度补全 (5 个缺失页面: Knowledge/Templates/ToolCatalog/Insights/Evaluation) | 已完成 | - | 代码审计 + Phase 3 教训 | frontend/ | - | 2026-02-13 |
| C-S2-7 | Opus 4.6 模型配置评估 (默认 Haiku 不变, 3 模型常量新增) | 已完成 | - | 外部技术变化 | constants.py + adapter | - | 2026-02-13 |
| C-S2-8 | logging 模块测试覆盖率 18%→100% | 已完成 | - | v1.6 代码审计 | shared/infrastructure/logging | - | 2026-02-13 |

#### S3 — 战略决策（Phase 4 期间）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S3-4 | A2A 协议采纳评估 (ADR) | 已完成 | M12 | 外部技术变化 | execution + 架构 | ADR 流程 | 2026-02-14 |
| C-S3-5 | 蓝绿部署引入时机评估 | 已完成 | M12 | Phase 3 教训 (v1.4 推迟) | infra/ | - | 2026-02-14 |
| C-S3-6 | Strands Agents vs claude-agent-sdk 战略评估 (ADR) | 已完成 | M12 | v1.6 外部技术扫描 | execution + 架构 | ADR 流程 | 2026-02-14 |

#### S4 — 中期改进（Phase 4 完成前）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S4-7 | Agent 镜像 CI/CD Pipeline 自动化 | 已完成 | P3-4 完成 | 代码审计 | .github/workflows/ | - | 2026-02-13 |
| C-S4-8 | Dev 环境定时缩减 (ECS Scheduled Scaling, UTC 12:00→0, UTC 00:00→1) | 已完成 | M11 | 成本优化 | infra/ | - | 2026-02-13 |
| C-S4-9 | 全项目文档更新 (API 文档 + 用户手册) | 已完成 | M12 | 推广需要 | docs/ | - | 2026-02-14 |

#### Phase 4 变更统计

| 级别 | 数量 | 时间窗口 | 当前进度 |
|------|:----:|---------|---------|
| S0 阻断修复 | 4 | M10-prep / M10 初 | **4/4 ✅** |
| S1 安全稳定 | 5 | M10 期间并行 | **5/5 ✅** |
| S2 技术债务 | 4 | M10-M11 穿插 | **4/4 ✅** |
| S3 战略决策 | 3 | Phase 4 期间 | **3/3 ✅** |
| S4 中期改进 | 3 | Phase 4 完成前 | **3/3 ✅** |
| **合计** | **19** | - | **19/19 ✅** |

---

## 遗留事项

1. ~~**Alembic 迁移待部署**~~ → ✅ 远程 Aurora 已通过 ECS 启动 CMD 自动执行（15 个迁移全部成功）
2. ~~**Agent Teams 端到端验证**~~ → ✅ 本地 + 远程均验证通过
3. ~~**远程部署验证**~~ → ✅ Dev 环境全链路验证通过（注册→登录→创建Agent→激活→SSE对话→Team Executions）
4. ~~**Claude Agent SDK 版本**~~ → ✅ 升级 0.1.3 → 0.1.35 (bundled CLI 2.1.39, 无需 Node.js)
5. ~~**SSE 流后 DB 写操作**~~ → ✅ 修复: 占位消息创建改用 stream_session（与 update 同一 session，消除跨事务可见性问题）
6. ~~**Sonnet 模型受限**~~ → ✅ 确认: `us.anthropic.claude-sonnet-4-20250514-v1:0` inference profile 状态 ACTIVE，Sonnet 可用 (prompt caching 限制不影响标准调用)
7. ~~**pytest-cov 缺失**~~ → ✅ 已安装 pytest-cov 7.0.0 + pytest-asyncio 1.3.0 + aiosqlite 0.22.1 + greenlet 3.3.1
8. ~~**test_database_defaults 测试失败**~~ → ✅ 修复: 所有 Settings 单元测试添加 `_env_file=None` 隔离 `.env` 文件，确保测试验证代码默认值而非环境覆盖值
9. ~~**OTEL instrumentation-sqlalchemy 安装问题**~~ → ✅ 根因: `python -m pytest` 调用了系统 Python 而非 uv 虚拟环境；统一使用 `uv run pytest` 后 1673 测试全通过
10. ~~**infra 快照测试过期**~~ → ✅ 快照已更新 + worker 泄漏修复 (workerIdleMemoryLimit)，161 测试全通过
11. ~~**前端覆盖度缺口**~~ → ✅ M10 已补全 5 个页面，覆盖度 45% → 85%
12. ~~**SDK 包名过时**~~ → ✅ 已确认: pyproject.toml 和所有 Python imports 已使用 `claude-agent-sdk` / `claude_agent_sdk`，无残留旧包名
13. ~~**CDK agentcore alpha BREAKING CHANGE**~~ → ✅ 已确认: 当前 `@aws-cdk/aws-bedrock-agentcore-alpha` 2.238.0-alpha.0 为最新版本，TypeScript 编译通过，Gateway User Pool Client API 无破坏性变更
14. ~~**Docker 本地构建待验证**~~ → ✅ 构建成功: `ai-agents-agent:latest` (701MB), 基础镜像改为 `public.ecr.aws` (修复 Docker Hub 连接问题)
15. ~~**Insights 前后端 API 不匹配**~~ → ✅ M11 #1-#6 修复: cost-breakdown/usage-trends/summary 端点补全; model_id 从事件传递; MessageReceivedEvent 订阅; 前端 3 图表对齐
16. ~~**Insights 数据采集不完整**~~ → ✅ 架构变更: 平台总成本依托 AWS Cost Explorer (真实账单), estimated_cost 弃用为 0.0, BedrockCostCalculator 标记弃用

### 部署信息

#### Dev 环境
- **后端 API**: `http://ai-agents-dev-546356512.us-east-1.elb.amazonaws.com`
- **Aurora 端点**: `ai-agents-plat-database-dev-auroraclusterd4efe71c-zmfookqjkiqn.cluster-cqm7um8tgaji.us-east-1.rds.amazonaws.com`
- **AgentCore Gateway**: `https://ai-agents-platform-gateway-dev-xbgpxlgiwl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp`
- **DB 凭证**: `dev/ai-agents-platform/db-credentials` (Secrets Manager)
- **ECS 配置**: 256 CPU / 512 MiB / 1 任务

#### Prod 环境
- **后端 API**: `http://ai-agents-prod-1419512933.us-east-1.elb.amazonaws.com`
- **Aurora 端点**: `ai-agents-plat-database-prod-auroraclusterd4efe71c-badfjgaibbbt.cluster-cqm7um8tgaji.us-east-1.rds.amazonaws.com`
- **AgentCore Gateway**: `https://ai-agents-platform-gateway-prod-rmpczcriio.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp`
- **DB 凭证**: `prod/ai-agents-platform/db-credentials` (Secrets Manager)
- **ECS 配置**: 512 CPU / 1024 MiB / 2 任务 | Aurora db.r6g.large (Writer + Reader)

---

## 近期会话

> 保留最近 5 条，超出时删除最旧记录。用于穿插计数、卡点检测和决策回溯。

| # | 日期 | 类型 | 完成项 | 关键决策 |
|---|------|------|-------|---------|
| 40 | 2026-02-14 | **M12 大幅推进** | **M12 #1-#12 完成 (Agent Teams 并行)**: 3 ADR (011 A2A 有限采纳 + 012 蓝绿暂缓 + 013 Strands 不迁移) + Identity OAuth/Token Vault + Memory Strategy/记忆注入 + A2A 适配器 + API 文档 9 文件 + locust 压测 + Onboarding 4 文件 + 推广计划; 变更积压清零 (Phase 4 19/19 ✅, P3 5/5 ✅) | ADR-011: A2A 有限采纳; ADR-012: 滚动增强; ADR-013: 不迁移 |
| 39 | 2026-02-14 | **M11 关闭** | **M11 全 13 任务完成**: #7 CDK 增强 (Performance Insights + S3 KnowledgeDocsBucket) + #8 灾备演练方案 (文档+2脚本) + #12 ADR-010 Opus 4.6 评估 + #13 质量验收; 2085+ 测试全通过; M11 关闭, 进入 M12 | ADR-010: 维持 Haiku 默认; 灾备 RPO<5min/RTO<15min |
| 38 | 2026-02-13 | M11 (D-E 完成) | **M11 #9/#10/#11 完成 (Agent Teams 并行)**: ECS Scheduled Scaling (Dev 成本降 50%) + Agent 预览端点 (execution 模块, §4.4 架构修正) + 前端测试面板/Prompt Editor 增强; SDK 升级 0.1.35+1.3.0; audit 导入修复; 1826 后端 + 167 infra 测试全通过 | preview 归 execution (职责域); AgentNotAvailableError (409) |
| 37 | 2026-02-13 | M11 (A-C 完成) | **M11 #1-#6 全部完成 (Agent Teams 并行)**: CostExplorerAdapter + model_id 修复 + MessageReceivedEvent 订阅 + 3 新端点 + 22 新测试 (96 总) + 前端 4 组件对齐; 1817 后端测试全通过 | 弃用 BedrockCostCalculator; estimated_cost=0.0; Cost Explorer 真实账单 |
| 36 | 2026-02-13 | M11 任务拆解 | **M11 13 任务拆解完成**: 深度探索 insights/execution/infra 现状; 发现前后端 API 不匹配; 砍掉 ROI 虚荣指标 + avg_response_time_ms 虚字段; 6 个工作流 A-F 并行策略 | insights 聚焦成本归因和使用量 (砍 ROI); 灾备/体验/评估并行 |
