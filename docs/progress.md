# 项目进度

> 每次 Claude Code 会话开始时读取此文件。会话结束时更新"当前状态"和"上次会话"。

## 当前状态

- **阶段**: Phase 1 MVP (0-3 月)
- **里程碑**: M3 端到端演示 — ✅ 已完成
- **下一步**: Phase 1 MVP 全部完成（后端+前端+基础设施+CI/CD）！可进入 Phase 2 或端到端集成部署

## 模块状态

### Phase 1 (0-3 月)

| 模块 | 状态 | 分支 | 备注 |
|------|:----:|------|------|
| `shared` | 已完成 | ai-agents-factory-v1 | PydanticEntity, IRepository, EventBus, DomainError, get_db, get_settings, PydanticRepository, exception_handlers, schemas |
| `auth` | 已完成 | ai-agents-factory-v1 | User, Role, JWT, RBAC, get_current_user, 登录/注册/me 端点 |
| `agents` | 已完成 | ai-agents-factory-v1 | Agent CRUD (7 端点), 状态机 (draft → active → archived), AgentConfig, 领域事件 |
| `execution` | 已完成 | ai-agents-factory-v1 | 单 Agent 对话 (6 端点), Bedrock ConverseStream, SSE 流式, IAgentQuerier 跨模块 |

### 后续阶段

| 阶段 | 模块 |
|------|------|
| Phase 2 | tools, knowledge, monitoring, templates |
| Phase 3 | orchestration, evaluation, models |
| Phase 4 | audit, marketplace, analytics |

## 基础设施

| CDK Stack | 状态 | 备注 |
|-----------|:----:|------|
| NetworkStack | 已完成 | VPC (3 AZ), Public/Private/Isolated Subnets, NAT Gateway (Dev:1/Prod:3), Flow Log, S3 Endpoint |
| SecurityStack | 已完成 | KMS 加密密钥 (轮换), API SG (443), DB SG (3306 仅 API), Prod Secrets Manager Endpoint |
| DatabaseStack | 已完成 | Aurora MySQL 3.x (PRIVATE_ISOLATED), Secrets Manager 凭证, 存储加密, IAM 认证 |

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

### M3: 端到端演示 (第 9-12 周) — ✅ 已完成

> 交付物: execution 模块完成（单 Agent 对话）+ SSE 流式响应 + 跨模块集成
> 验收标准: ruff check + mypy --strict + pytest --cov-fail-under=85 全通过；用户可与 ACTIVE Agent 对话
> 验收结果: **611 测试通过，覆盖率 94.08%，ruff/mypy 全通过，架构合规全通过**

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

---

## 遗留事项

(当前无代码缺陷遗留)

### 部署注意事项

- Alembic migration 已配置并通过 `alembic history` 验证，但未连接实际 MySQL 运行 `alembic upgrade head`，首次部署时需验证

---

## 上次会话

> 仅保留最近一次，每次会话结束时覆盖更新此节。

- **日期**: 2026-02-09
- **完成**: Phase 1 MVP 全部完成 — 后端(M1-M3 + 安全加固) + 前端(FSD React) + 基础设施(CDK 3 Stacks) + CI/CD(3 GitHub Actions)。本次会话完成: 基础设施 CDK 开发（4 波 Agent Teams: scaffold → dev-network+dev-security 并行 → dev-database+CI/CD → reviewer），41 文件，73 测试，100% 覆盖率，CDK Nag 合规
- **决策**: VPC 3 AZ 三层子网 (Public/Private/Isolated)；Dev 单 NAT Gateway 节省成本；Aurora MySQL PRIVATE_ISOLATED + KMS 加密 + Secrets Manager 凭证；CDK Nag AwsSolutionsChecks 资源级抑制（非 Stack 级）；Stack 间 Props 传递依赖（非 CfnOutput）
