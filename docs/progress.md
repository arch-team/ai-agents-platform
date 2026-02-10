# 项目进度

> 每次 Claude Code 会话开始时读取此文件。会话结束时更新"当前状态"和"上次会话"。

## 当前状态

- **阶段**: Phase 2 核心功能 (3-6 月)
- **里程碑**: M5 知识库 — ✅ 已完成
- **变更积压**: S0 ✅ + 4 S1 + 3 S2 + 2 S3 + 5 S4 = 14 项 | AgentCore 集成: P0 (0/6) + P1 (0/4) + P2 (0/3) + P3 (0/3) = 16 项
- **关键决策**: ADR-006 已采纳 — Agent 框架选型: Claude Agent SDK + Claude Code CLI (单一框架)
- **下一步**: 执行 AgentCore 集成 P0 基础就绪 (依赖升级 → 接口定义 → runtime_type → 可观测性基础)，与 M6 拆解并行

## 模块状态

### Phase 1 (0-3 月)

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| `shared` | 已完成 | ai-agents-factory-v1 | PydanticEntity, IRepository, EventBus, DomainError, get_db, get_settings, PydanticRepository, exception_handlers, schemas |
| `auth` | 已完成 | ai-agents-factory-v1 | User, Role, JWT, RBAC, get_current_user, 登录/注册/me 端点 |
| `agents` | 已完成 | ai-agents-factory-v1 | Agent CRUD (7 端点), 状态机 (draft → active → archived), AgentConfig, 领域事件 |
| `execution` | 已完成 | ai-agents-factory-v1 | 单 Agent 对话 (6 端点), Bedrock ConverseStream, SSE 流式, IAgentQuerier 跨模块。**待升级**: ADR-006 → IAgentRuntime + StrandsAgentAdapter |

### Phase 2 (3-6 月)

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| `tool-catalog` | 已完成 | ai-agents-factory-v1 | 工具注册/审批 (10 端点), 5 状态审批流程, MCP Server/API/Function 三类工具 |
| `knowledge` | 已完成 | ai-agents-factory-v1 | 知识库管理, RAG 检索 (Bedrock Knowledge Bases, ADR-005), 10 端点 |
| `insights` | 待开始 | - | 成本归因, 使用趋势 |
| `templates` | 待开始 | - | Agent 模板管理 (依赖 tool-catalog + knowledge) |

### 后续阶段

| 阶段 | 模块 |
|------|------|
| Phase 3 | orchestration, evaluation |
| Phase 4 | audit, marketplace, analytics |

## 基础设施

| CDK Stack | 状态 | 备注 |
|-----------|:----:|------|
| NetworkStack | 已完成 | VPC (3 AZ), Public/Private/Isolated Subnets, NAT Gateway (Dev:1/Prod:3), Flow Log, S3 Endpoint |
| SecurityStack | 已完成 | KMS 加密密钥 (轮换), API SG (443), DB SG (3306 仅 API), Prod Secrets Manager Endpoint |
| DatabaseStack | 已完成 | Aurora MySQL 3.x (PRIVATE_ISOLATED), Secrets Manager 凭证, 存储加密, IAM 认证 |
| AgentCoreStack | 待开始 | AgentCore Runtime + Gateway CDK 资源 (ADR-006, P1-3) |

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
| C-S1-1 | 登录 Rate Limiting + 账户锁定 | 待开始 | - | 安全审查 SEC4+SEC5 (高危) | auth + 中间件 | `improvement-plan.md` §3 S1-1 | - |
| C-S1-2 | Refresh Token 机制 | 待开始 | - | 安全审查 SEC2+SEC3 (高危) | auth 模块 | `improvement-plan.md` §3 S1-2 | - |
| C-S1-3 | 基础安全审计日志 | 待开始 | - | 安全审查 SEC7 (高危) | auth + shared | `improvement-plan.md` §3 S1-3 | - |
| C-S1-4 | 注册端点权限保护 | 待开始 | - | 安全审查 SEC16 (中危) | auth API | `improvement-plan.md` §3 S1-4 | - |
| C-S1-5 | CORS 运行时校验 | 已完成 | C-S0-6 | 安全审查 SEC17 (中危) | shared/settings | `improvement-plan.md` §3 S1-5 | 2026-02-10 |

### S2 — 性能解锁（M5 开发期间并行）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S2-1 | 自定义线程池 + 连接池调优 | 待开始 | C-S0-1 | 性能审查 PERF1+PERF3 (HIGH) | shared/database + execution | `improvement-plan.md` §4 S2-1 | - |
| C-S2-2 | 对话历史滑动窗口 | 待开始 | - | 性能审查 PERF4 (CRITICAL) | execution 模块 | `improvement-plan.md` §4 S2-2 | - |
| C-S2-3 | EventBus 内存泄漏修复 | 已完成 | - | 性能审查 PERF9 + 架构审查 A3 | shared/event_bus | `improvement-plan.md` §4 S2-3 | 2026-02-10 |
| C-S2-4 | Agent 配置本地缓存 | 待开始 | - | 性能审查 PERF8 (HIGH) | agents 模块 | `improvement-plan.md` §4 S2-4 | - |

### S3 — 战略决策（M5 启动前）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S3-1 | MySQL vs PostgreSQL 技术选型 (ADR) | 已完成 | - | DevOps D4 + 性能 PERF10 | 全项目数据库 | `improvement-plan.md` §5 S3-1 | 2026-02-10 |
| C-S3-2 | 端到端集成验证 (M4.5) | 待开始 | C-S0-3 | 产品审查 P2 | 前后端联调 | `improvement-plan.md` §5 S3-2 | - |
| C-S3-3 | 路线图调整评审 | 待开始 | C-S3-1 | 产品审查 P1+P3+P10 | roadmap.md | `improvement-plan.md` §5 S3-3 | - |

### S4 — 中期改进（Phase 2 完成前）

| 编号 | 变更描述 | 状态 | 依赖 | 来源 | 影响范围 | 参考规范 | 会话 |
|------|---------|:----:|:----:|------|---------|---------|------|
| C-S4-1 | CI/CD Pipeline 完善 | 待开始 | C-S0-3, C-S0-4 | DevOps 审查 D3 | .github/workflows/ | `improvement-plan.md` §6 S4-1 | - |
| C-S4-2 | CDK 首次部署验证 | 待开始 | C-S0-3 | DevOps 审查 D1 (阻塞级) | infra/ | `improvement-plan.md` §6 S4-2 | - |
| C-S4-3 | Secrets 管理统一 | 待开始 | C-S0-6 | DevOps 审查 D6 | shared/settings + infra | `improvement-plan.md` §6 S4-3 | - |
| C-S4-4 | 基础监控告警 | 待开始 | C-S4-2 | DevOps 审查 D8 | infra/ CDK | `improvement-plan.md` §6 S4-4 | - |
| C-S4-5 | python-jose 迁移到 PyJWT | 待开始 | - | 安全审查 SEC19 | auth 模块 | `improvement-plan.md` §6 S4-5 | - |

### 变更统计

| 级别 | 数量 | 时间窗口 | 当前进度 |
|------|:----:|---------|---------|
| S0 阻断修复 | 6 | 进入 M5 之前 | **6/6 ✅** |
| S1 安全加固 | 5 | M5 开发期间并行 | 1/5 |
| S2 性能解锁 | 4 | M5 开发期间并行 | 1/4 |
| S3 战略决策 | 3 | M5 启动前决策 | 1/3 |
| S4 中期改进 | 5 | Phase 2 完成前 | 0/5 |
| **合计** | **23** | - | **9/23** |

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

> P2/P3 行动项（Gateway、Memory、Observability、Claude Agent SDK 等）详见 `agentcore-integration-plan.md` §4-5，Phase 3 前启动。

| 级别 | 数量 | 时间窗口 | 当前进度 |
|------|:----:|---------|---------|
| P0 基础就绪 | 6 | M6 之前 | **6/6 ✅** |
| P1 核心集成 | 4 | M6 期间 | **4/4 ✅** |
| P2 平台能力 | 3 | Phase 3 前 | 0/3 |
| P3 深度集成 | 3 | Phase 3-4 | 0/3 |
| **合计** | **16** | - | **10/16** |

---

## 遗留事项

(当前无代码缺陷遗留)

### 部署注意事项

- Alembic migration 已配置并通过 `alembic history` 验证，但未连接实际 MySQL 运行 `alembic upgrade head`，首次部署时需验证

---

## 近期会话

> 保留最近 5 条，超出时删除最旧记录。用于穿插计数、卡点检测和决策回溯。

| # | 日期 | 类型 | 完成项 | 关键决策 |
|---|------|------|-------|---------|
| 14 | 2026-02-10 | AgentCore 集成 | **P0 全完成 (6/6) + P1 全完成 (4/4)** — 965 测试, ClaudeAgentAdapter + ExecutionService 路由 + AgentCore CDK + 入口点 | Agent Teams 并行; Claude Agent SDK → CLI → Bedrock Invoke API |
| 13 | 2026-02-10 | 架构决策 | **ADR-006 Agent 框架选型** + AgentCore 集成行动计划 (16 项 P0-P3) | Claude Agent SDK + Claude Code CLI 单一框架; agentcore-integration-plan.md |
| 12 | 2026-02-10 | Milestone | **M5 知识库完成** 14/14 任务, 1023 测试, 覆盖率 95.10% | 26 集成测试 (15 Repo + 11 API); knowledge 模块交付 |
| 11 | 2026-02-10 | Milestone | M5 #9-#11 API+注册+RAG集成, 997 测试 | 10 端点; RAG 上下文注入 |
| 10 | 2026-02-10 | Milestone | M5 #6-#8 Infrastructure, 994 测试 | ORM; Bedrock; S3 |
