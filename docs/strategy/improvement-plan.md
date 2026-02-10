# 改进行动计划 (Improvement Action Plan)

> **来源**: 五维度项目深度审查（架构、安全、产品、基础设施、性能）
> **审查日期**: 2026-02-10
> **状态**: 初始版本 — 待团队评审

---

## 0. 审查概述

### 审查维度与发现

| 维度 | 审查角色 | 发现总数 | 关键数量 |
|------|---------|---------|---------|
| 架构设计 | 架构师 | 8 项 | 2 个 P0 + 2 个 P1 |
| 安全实践 | 安全工程师 | 26 项 | 10 个高危 + 13 个中危 |
| 产品战略 | 产品/商业分析 | 10 项 | 3 个战略级 |
| 基础设施/DevOps | DevOps 架构师 | 10 项 | 3 个阻塞级 + 4 个重要 |
| 性能/可扩展性 | 性能工程师 | 10 项 | 1 个 CRITICAL + 4 个 HIGH |

### 核心结论

1. **"质量高"与"可部署"之间存在鸿沟** — 842 测试 / 94.65% 覆盖率建立在 SQLite 之上，CDK 从未实际部署，无 Dockerfile
2. **并发天花板极低** — 默认线程池(8) + 默认连接池(15) + SSE 长连接 = 仅支撑 8 个并发流式对话
3. **安全基线不足** — 无账户锁定、无 Rate Limiting、无审计日志、is_active 未校验
4. **技术选型决策点** — MySQL vs PostgreSQL 直接影响 knowledge(RAG) 模块，需尽快决策

---

## 1. 行动分级

### 分级标准

| 级别 | 定义 | 时间要求 |
|------|------|---------|
| **S0 — 阻断修复** | 正确性缺陷或阻塞部署路径，不修复无法继续 | 进入 M5 之前 |
| **S1 — 安全加固** | 高危安全漏洞，影响企业合规和资产安全 | M5 开发期间并行 |
| **S2 — 性能解锁** | 并发瓶颈和资源泄漏，影响多用户使用 | M5 开发期间并行 |
| **S3 — 战略决策** | 技术选型和产品方向，影响后续 Phase 规划 | M5 启动前决策 |
| **S4 — 中期改进** | 架构优化和工程实践提升 | Phase 2 完成前 |
| **S5 — 长期规划** | 架构演进和产品战略调整 | 按季度评审 |

---

## 2. S0 — 阻断修复（进入 M5 之前）

### S0-1: 修复 SSE 流式 session 生命周期缺陷

**来源**: 架构审查 #1 (P0)

**问题**: `StreamingResponse` 返回后，FastAPI 的 `Depends(get_db)` session 生命周期结束（`async with` 在 yield 后关闭），但 `send_message_stream` 的 async generator 内部仍通过该 session 执行数据库写操作（`_message_repo.update`、`_conversation_repo.update`），导致 session 已关闭后的写入失败或数据丢失。

**影响文件**:
- `backend/src/modules/execution/application/services/execution_service.py:171-272`
- `backend/src/modules/execution/api/endpoints.py:130-159`
- `backend/src/modules/execution/api/dependencies.py:32-45`

**修复方案**:
1. 在 `event_generator()` 内部独立管理数据库 session（不依赖 FastAPI DI）
2. 流式传输完成后，使用独立 session 执行数据库写操作
3. 添加连接断开检测和超时机制

**验证标准**: 流式对话完成后，数据库中正确记录 assistant message 和 token 统计；并发 10 个流式请求无数据丢失。

---

### S0-2: 修复 Alembic 迁移 ID 冲突

**来源**: 架构审查 #7 (P0)

**问题**: `b2c3d4e5f6a7_create_conversations_and_messages_tables.py` 和 `b2c3d4e5f6a7_create_tools_table.py` 使用相同的 revision ID，`alembic upgrade head` 直接失败。

**影响文件**:
- `backend/migrations/versions/b2c3d4e5f6a7_create_conversations_and_messages_tables.py`
- `backend/migrations/versions/b2c3d4e5f6a7_create_tools_table.py`

**修复方案**:
1. 为 tools 迁移生成新的 revision ID
2. 建立正确的迁移链: users → agents → conversations/messages → tools
3. 使用 `alembic revision --autogenerate` 重新生成，避免手工 ID
4. 在 CI 中添加 `alembic check` 验证迁移链完整性

**验证标准**: `alembic upgrade head` 在全新数据库上成功执行；`alembic history` 显示线性迁移链。

---

### S0-3: 创建 Dockerfile 和 docker-compose

**来源**: DevOps 审查 #7 (阻塞级)

**问题**: 项目无 Dockerfile、无 docker-compose，Phase 2 目标 ECS Fargate 部署无法实现；同时阻碍基于 MySQL 的集成测试。

**交付物**:
1. `backend/Dockerfile` — 多阶段构建（builder + runtime），基于 `python:3.12-slim`
2. `docker-compose.yml` — MySQL 8.0 + 后端服务 + 可选前端
3. `backend/.dockerignore` — 排除测试、文档、IDE 配置
4. `scripts/docker-dev.sh` — 一键启动本地开发环境

**验证标准**: `docker-compose up` 启动后，后端 health check 返回 200；`alembic upgrade head` 在 MySQL 容器上成功执行。

---

### S0-4: 添加 MySQL 集成测试

**来源**: DevOps 审查 #2 (阻塞级)

**问题**: 所有集成测试使用 `sqlite+aiosqlite:///:memory:`，与生产 MySQL 存在 5+ 方言差异（大小写敏感性、外键约束、事务隔离、JSON 支持、日期时间处理）。

**修复方案**:
1. 在 `docker-compose.yml` 中配置 MySQL 8.0 test 容器
2. 新增 pytest marker `@pytest.mark.mysql` 标记需要 MySQL 的测试
3. 更新 `backend-ci.yml` 添加 MySQL service container
4. 关键仓库测试（Repository + API 集成测试）同时运行 SQLite 和 MySQL 两套

**验证标准**: CI 中 MySQL 集成测试通过；覆盖所有 Repository 和 API 端点测试。

---

### S0-5: 修复 `get_current_user` 未检查 `is_active`

**来源**: 安全审查 #11 (中危，但修复成本极低)

**问题**: `get_current_user` 从数据库获取用户后只检查 `user is None`，不检查 `is_active` 状态。被停用用户只要 Token 有效仍可访问系统。

**影响文件**:
- `backend/src/modules/auth/api/dependencies.py:38-62`

**修复方案**: 添加 `if not user.is_active: raise AuthenticationError("账户已停用")`。

**验证标准**: 停用用户持有有效 Token 时请求返回 401。

---

### S0-6: JWT Secret 启动校验

**来源**: 安全审查 #1 (高危，修复成本极低)

**问题**: `JWT_SECRET_KEY` 默认值为 `"changeme"`，生产环境忘记配置时将使用弱密钥。

**影响文件**:
- `backend/src/shared/infrastructure/settings.py:30`

**修复方案**: 在 `Settings` 中添加 `@model_validator(mode='after')` 校验 `JWT_SECRET_KEY` 不是默认值（或长度 < 32 字符），非开发环境启动时 fail-fast。

**验证标准**: `APP_ENV=production` 且 `JWT_SECRET_KEY=changeme` 时应用启动失败并输出明确错误信息。

---

## 3. S1 — 安全加固（M5 开发期间并行）

### S1-1: 登录 Rate Limiting + 账户锁定

**来源**: 安全审查 #4 + #5 (高危)

**问题**: 无登录失败计数器和锁定逻辑（规范要求 5 次失败锁定 30 分钟但未实现），无全局 Rate Limiting。

**实现方案**:
1. 添加 `slowapi` 或自定义 Rate Limiting 中间件
2. 登录端点: 5 次/分钟/IP（或 5 次失败后锁定 30 分钟）
3. LLM 对话端点: 10 次/分钟/用户
4. 注册端点: 3 次/小时/IP
5. 在 User 实体或独立表中记录 `failed_login_count` 和 `locked_until`

**影响文件**:
- `backend/src/modules/auth/application/services/user_service.py` (login 方法)
- `backend/src/presentation/api/main.py` (中间件注册)
- 新增: Rate Limiting 中间件

**验证标准**: 6 次错误密码后返回 429；锁定期间正确密码也返回 423。

---

### S1-2: Refresh Token 机制

**来源**: 安全审查 #2 + #3 (高危)

**问题**: 仅发放 Access Token，30 分钟过期需重新登录；SSE 长连接中 Token 可能过期。

**实现方案**:
1. 登录时同时返回 `access_token`（15 分钟）+ `refresh_token`（7 天）
2. `POST /api/v1/auth/refresh` 端点用 refresh_token 换发新 access_token
3. refresh_token 存数据库（支持撤销）
4. 用户被停用或角色变更时，使其所有 refresh_token 失效

**影响文件**:
- `backend/src/modules/auth/application/services/user_service.py`
- `backend/src/modules/auth/api/endpoints.py`
- 新增: RefreshToken 实体 + Repository

**验证标准**: access_token 过期后可通过 refresh_token 获取新 token；用户停用后 refresh 返回 401。

---

### S1-3: 基础安全审计日志

**来源**: 安全审查 #7 (高危)

**问题**: 无任何安全事件记录。作为 MVP 安全基线，至少需记录认证和授权事件。

**实现方案**:
1. 使用 structlog 记录以下安全事件（不新建模块，仅添加日志）:
   - 登录成功/失败（IP、User-Agent、user_id）
   - 注册（IP、email）
   - Token 签发
   - 权限拒绝（403）
   - 用户停用/激活
2. 日志格式: `logger.info("security_event", event_type="login_success", user_id=..., ip=...)`
3. 后续 Phase 4 的 audit 模块可消费这些结构化日志

**验证标准**: 登录成功/失败均产生 structlog 安全事件日志，包含 IP 和 user_id。

---

### S1-4: 注册端点权限保护

**来源**: 安全审查 #16 (中危)

**问题**: 注册端点完全公开，任何人可注册企业内部平台账户。

**实现方案**: 两个可选方案（需 ADR 决策）:
- **方案 A**: 邀请码注册 — ADMIN 生成邀请码，注册时验证
- **方案 B**: 环境变量开关 — `REGISTRATION_ENABLED=false` 时关闭注册，仅 ADMIN 可通过管理接口创建用户

**验证标准**: 非授权注册请求返回 403 或 404。

---

### S1-5: CORS 运行时校验

**来源**: 安全审查 #17 (中危)

**问题**: `allow_credentials=True` 时未校验 `allow_origins` 不能为 `["*"]`。

**影响文件**:
- `backend/src/shared/infrastructure/settings.py`

**修复方案**: 在 `Settings` 的 `@model_validator` 中校验 `CORS_ALLOWED_ORIGINS` 不包含 `"*"`。

**验证标准**: `CORS_ALLOWED_ORIGINS=["*"]` 时应用启动失败。

---

## 4. S2 — 性能解锁（M5 开发期间并行）

### S2-1: 自定义线程池 + 连接池调优

**来源**: 性能审查 #1 + #3 (HIGH)

**问题**: 默认线程池 8 + 默认连接池 15，系统并发上限仅 8 个 SSE 连接。

**修复方案**:

数据库连接池（`database.py`）:
```
pool_size=20, max_overflow=30, pool_timeout=30, pool_recycle=1800
```

Bedrock 客户端专用线程池:
```
bedrock_executor = ThreadPoolExecutor(max_workers=50, thread_name_prefix="bedrock")
loop.run_in_executor(bedrock_executor, ...)
```

**影响文件**:
- `backend/src/shared/infrastructure/database.py`
- `backend/src/modules/execution/infrastructure/external/bedrock_llm_client.py`

**验证标准**: 30 个并发 SSE 请求稳定响应，无超时错误。

---

### S2-2: 对话历史滑动窗口

**来源**: 性能审查 #4 (CRITICAL)

**问题**: `send_message` 加载完整对话历史传给 LLM，无 Context Window 管理。100 条消息可达 30K-100K tokens，成本爆炸且可能超出模型上下文限制。

**实现方案**:
1. `ExecutionService` 中添加 `max_context_tokens` 配置（默认 30000）
2. 从最新消息往前截取，累计 token 数不超过预算
3. 预留 system_prompt token 预算
4. 超长对话给出提示，建议用户创建新对话

**影响文件**:
- `backend/src/modules/execution/application/services/execution_service.py`
- `backend/src/shared/infrastructure/settings.py` (新增配置)

**验证标准**: 100 条消息的对话发送新消息时，LLM 收到的消息数 < 100；总 token 数在预算内。

---

### S2-3: EventBus 内存泄漏修复

**来源**: 性能审查 #9 + 架构审查 #3 (HIGH + P1)

**问题**: `_processed_event_ids` 是只增不减的 set，约 180MB/月增长；多 worker 部署时事件丢失。

**修复方案**:
1. 短期: 将 `set` 替换为 `cachetools.TTLCache(maxsize=100000, ttl=3600)` — 1 小时后自动过期
2. 中期: 评估是否需要 Outbox Pattern（结合 S4-3 架构演进一起决策）

**影响文件**:
- `backend/src/shared/domain/event_bus.py`
- `backend/pyproject.toml` (添加 cachetools 依赖)

**验证标准**: 长时间运行后内存稳定，不持续增长；TTLCache 超时后重复事件 ID 可重新处理。

---

### S2-4: Agent 配置本地缓存

**来源**: 性能审查 #8 (HIGH)

**问题**: 每次 `send_message` 都查询 Agent 配置（`get_active_agent`），但 Agent 配置变更频率极低。

**实现方案**:
1. 在 `AgentQuerierImpl` 中添加 TTL 缓存（`cachetools.TTLCache(maxsize=500, ttl=300)`）
2. 缓存 key 为 `agent_id`，5 分钟过期
3. Agent 配置更新时可通过事件主动失效（可选，Phase 2+）

**影响文件**:
- `backend/src/modules/agents/infrastructure/services/agent_querier_impl.py`

**验证标准**: 同一 Agent 连续 10 次对话只产生 1 次数据库查询。

---

## 5. S3 — 战略决策（M5 启动前）

### S3-1: MySQL vs PostgreSQL 技术选型 (ADR)

**来源**: DevOps 审查 #4 + 性能审查 #10

**问题**: Aurora MySQL 不支持向量搜索，Phase 2 的 knowledge(RAG) 模块需要额外向量存储。

**决策选项**:

| 选项 | 优势 | 劣势 | 迁移成本 |
|------|------|------|---------|
| **A: MySQL + OpenSearch** | 无需迁移关系库；OpenSearch 是 AWS 原生向量方案 | 双数据源同步复杂；新增 CDK Stack 和运维成本 | 低（新增） |
| **B: MySQL + Bedrock Knowledge Bases** | 全托管 RAG；零运维向量存储 | 厂商锁定加深；灵活性受限 | 低（新增） |
| **C: 迁移到 PostgreSQL + pgvector** | 单数据源；pgvector 成熟；社区生态更好 | 所有 ORM 和迁移需修改；asyncmy → asyncpg | 高但当前数据为空 |

**决策要素**:
- 当前数据库为空（4 个模块已完成但未部署），迁移成本尚可
- PostgreSQL 对 JSON 查询、数组类型的支持优于 MySQL
- pgvector 的 HNSW 索引性能已达生产级别
- 长期来看 PostgreSQL 更适合 AI 应用场景

**交付物**: `docs/adr/005-database-engine-selection.md`

**截止日期**: M5 knowledge 模块设计前

---

### S3-2: 端到端集成验证 (M4.5)

**来源**: 产品审查 #2

**问题**: Phase 1 后端"已完成"但无真实用户能使用产品。前端已有完整实现但未纳入进度跟踪。

**行动项**:
1. 前后端联调: 确保 `登录 → 创建 Agent → 发送对话 → 查看回复` 完整链路跑通
2. 基于 docker-compose（S0-3）搭建本地全栈环境
3. 邀请 3-5 名目标用户进行内部试用
4. 收集反馈，调整 M5 优先级

**交付物**: 可运行的端到端 Demo 环境 + 用户反馈记录

---

### S3-3: 路线图调整评审

**来源**: 产品审查 #1 + #3 + #10

**核心质疑**:
- 24 个月路线图在 AI 快速迭代时代是否过长？
- knowledge 模块是否应优先于 insights？
- Phase 4 的 marketplace 和多区域部署是否过度规划？

**建议调整**:

| 原规划 | 调整建议 | 理由 |
|--------|---------|------|
| Phase 2: tool-catalog → knowledge → insights → templates | tool-catalog(已完成) → **knowledge** → templates → insights | RAG 是 Agent 核心能力，比成本统计更紧迫 |
| Phase 4: marketplace + 多区域 + 灾备 | **降级或移除** marketplace 和多区域 | 200 人内部平台不需要市场机制和多区域部署 |
| 24 个月固定路线图 | 改为 **12 个月滚动规划 + 季度评审** | AI 领域变化快，Phase 3/4 仅保留方向性描述 |
| RPO < 1s, RTO < 1min | 调整为 **RPO < 5min, RTO < 15min** | 内部平台不需要金融级灾备 |

**交付物**: 更新后的 `docs/strategy/roadmap.md` + 季度评审机制

---

## 6. S4 — 中期改进（Phase 2 完成前）

### S4-1: CI/CD Pipeline 完善

**来源**: DevOps 审查 #3

**当前状态**: 3 个 GitHub Actions 工作流存在但不完整。

**补充项**:
1. `backend-ci.yml` 添加 MySQL service container 运行集成测试
2. `backend-ci.yml` 添加 `bandit` + `safety` + `pip-audit` 安全扫描步骤
3. `backend-ci.yml` 锁定 `uv` 版本，添加依赖缓存
4. `cdk-deploy.yml` 添加 `cdk diff` 步骤（PR 自动评论变更内容）
5. `cdk-deploy.yml` 添加 staging 和 prod 部署 job（含审批门控）
6. 配置 Dependabot 或 Renovate 依赖自动更新

---

### S4-2: CDK 首次部署验证

**来源**: DevOps 审查 #1 (阻塞级)

**行动项**:
1. 配置真实 AWS 账户 ID（替换 `cdk.json` 占位符）
2. 执行 `cdk deploy --all` 到 Dev 环境
3. 验证 VPC、Security Groups、Aurora 集群实际创建成功
4. 运行 `alembic upgrade head` 到实际 MySQL
5. 部署后端服务到 ECS Fargate（使用 S0-3 的 Dockerfile）
6. 端到端验证 API 可用性

---

### S4-3: Secrets 管理统一

**来源**: DevOps 审查 #6

**问题**: CDK 使用 Secrets Manager，应用使用 .env 文件，两套配置不同步。

**修复方案**:
1. 应用启动时从 Secrets Manager 读取 Aurora 凭证（非环境变量传递明文密码）
2. JWT Secret 也存入 Secrets Manager
3. ECS Task 通过 IAM Role 获取 AWS 凭证（移除 .env 中的 AK/SK）
4. 本地开发仍使用 .env（通过 `APP_ENV` 区分读取路径）

---

### S4-4: 基础监控告警

**来源**: DevOps 审查 #8

**最小可行监控**:
1. Aurora CloudWatch Alarm: CPU > 80%, FreeableMemory < 500MB, ConnectionCount > 80%
2. ECS Alarm: CPU > 80%, MemoryUtilization > 80%
3. SNS Topic + Email 通知
4. 基础 CloudWatch Dashboard（数据库 + 应用关键指标）

---

### S4-5: python-jose 迁移

**来源**: 安全审查 #19

**问题**: `python-jose` 最后版本 3.3.0 发布于 2021 年，处于半维护状态。

**修复方案**: 迁移到 `PyJWT`（更活跃维护、社区更广泛）。接口变更小，主要是 `encode/decode` 函数签名差异。

---

## 7. S5 — 长期规划（按季度评审）

### S5-1: EventBus 可靠性升级

评估是否需要从进程内 EventBus 升级到持久化方案（Outbox Pattern + 后台发布）。判断标准:
- 如果 Phase 3 orchestration 模块需要跨服务事件 → 升级
- 如果保持单体部署且事件仅用于解耦 → 当前方案（加 TTLCache）已够用

### S5-2: 数据库加密

评估对话内容列级加密或 Application-level encryption 方案。需平衡性能影响和合规需求。

### S5-3: DDD 分层简化评估

评估对行为贫乏的实体（Message、Tool）是否可简化 DDD 层级，减少样板代码。

### S5-4: RBAC 细化评估

评估三角色模型是否需要升级为自定义角色或 ABAC。触发条件: 用户规模超过 50 人或出现角色不足的反馈。

### S5-5: shared/ 接口治理

制定 `shared/domain/interfaces/` 的准入标准，防止跨模块接口堆积导致 shared 模块膨胀。考虑 Consumer-Driven Contract 模式。

---

## 8. 进度跟踪

### 执行节奏

| 级别 | 时间窗口 | 跟踪方式 |
|------|---------|---------|
| S0 | 本周完成 | `docs/progress.md` 每日更新 |
| S1 + S2 | M5 开发期间并行 | `docs/progress.md` 任务表 |
| S3 | M5 启动前决策 | ADR 文档 + 团队评审 |
| S4 | Phase 2 结束前 | `docs/progress.md` 里程碑 |
| S5 | 季度评审 | 本文档更新 |

### S0 检查清单

- [ ] S0-1: SSE 流式 session 生命周期修复
- [ ] S0-2: Alembic 迁移 ID 冲突修复
- [ ] S0-3: Dockerfile + docker-compose 创建
- [ ] S0-4: MySQL 集成测试添加
- [ ] S0-5: `get_current_user` 添加 `is_active` 检查
- [ ] S0-6: JWT Secret 启动校验

### S1 检查清单

- [ ] S1-1: 登录 Rate Limiting + 账户锁定
- [ ] S1-2: Refresh Token 机制
- [ ] S1-3: 基础安全审计日志
- [ ] S1-4: 注册端点权限保护（ADR 决策方案）
- [ ] S1-5: CORS 运行时校验

### S2 检查清单

- [ ] S2-1: 自定义线程池 + 连接池调优
- [ ] S2-2: 对话历史滑动窗口
- [ ] S2-3: EventBus 内存泄漏修复
- [ ] S2-4: Agent 配置本地缓存

### S3 检查清单

- [ ] S3-1: MySQL vs PostgreSQL ADR
- [ ] S3-2: 端到端集成验证 (M4.5)
- [ ] S3-3: 路线图调整评审

---

## 附录: 问题溯源表

> 完整发现列表，按维度和严重程度排列。

### 架构维度

| # | 问题 | 严重程度 | 行动编号 |
|---|------|---------|---------|
| A1 | SSE 流式 session 生命周期缺陷 | P0 | S0-1 |
| A2 | Alembic 迁移 ID 冲突 | P0 | S0-2 |
| A3 | EventBus 内存泄漏 + 多 worker 失效 | P1 | S2-3 |
| A4 | asyncio.to_thread 阻塞事件循环 | P1 | S2-1 |
| A5 | 双重模型转换静默丢字段 | P2 | S5-3 |
| A6 | shared/ 业务语义渗透 | P2 | S5-5 |
| A7 | providers.py 膨胀风险 | P3 | S5-5 |
| A8 | DDD 对简单模块过度设计 | P3 | S5-3 |

### 安全维度

| # | 问题 | 严重程度 | 行动编号 |
|---|------|---------|---------|
| SEC1 | JWT Secret 弱默认值 | 高危 | S0-6 |
| SEC2 | 无 Refresh Token | 高危 | S1-2 |
| SEC3 | 无 Token 撤销/黑名单 | 高危 | S1-2 |
| SEC4 | 无账户锁定 | 高危 | S1-1 |
| SEC5 | 全局无 Rate Limiting | 高危 | S1-1 |
| SEC6 | 无 LLM Token 消耗配额 | 高危 | S1-1 |
| SEC7 | 无安全审计日志 | 高危 | S1-3 |
| SEC8 | 对话内容明文存储 | 高危 | S5-2 |
| SEC9 | SSE 长连接无 Token 续期 | 高危 | S1-2 |
| SEC10 | AWS 凭证管理不明确 | 高危 | S4-3 |
| SEC11 | get_current_user 不检查 is_active | 中危 | S0-5 |
| SEC12 | JWT 中嵌入角色信息泄露 | 中危 | S4-5 |
| SEC13 | HS256 对称算法 | 中危 | S5-4 |
| SEC14 | 三角色模型粗糙 | 中危 | S5-4 |
| SEC15 | Tool allowed_roles 未执行 | 中危 | S4 范围 |
| SEC16 | 注册端点无权限保护 | 中危 | S1-4 |
| SEC17 | CORS 无运行时校验 | 中危 | S1-5 |
| SEC18 | 数据库连接未强制 TLS | 中危 | S4-3 |
| SEC19 | python-jose 维护状态 | 中危 | S4-5 |
| SEC20 | Settings 密钥无法热更新 | 中危 | S4-3 |
| SEC21 | User ID 自增整数可枚举 | 中危 | S5 范围 |
| SEC22 | SSE 错误泄露领域信息 | 中危 | S4 范围 |
| SEC23 | DATABASE_PASSWORD 弱默认值 | 中危 | S0-6 |
| SEC24 | 密码不要求特殊字符 | 低危 | S5 范围 |
| SEC25 | bcrypt rounds 硬编码 | 低危 | S5 范围 |
| SEC26 | 异常处理用 logging 非 structlog | 低危 | S4 范围 |

### 产品维度

| # | 问题 | 行动编号 |
|---|------|---------|
| P1 | 24 个月路线图过长 | S3-3 |
| P2 | MVP ≠ 可用产品 | S3-2 |
| P3 | RAG 排序合理性 | S3-3 |
| P4 | 用户增长假设缺乏依据 | S3-3 |
| P5 | ROI 未量化 | S3-3 |
| P6 | 前后端开发节奏脱节 | S3-2 |
| P7 | "10+ Agent 模板"质量标准 | S3-3 |
| P8 | Phase 4 自助式假设乐观 | S3-3 |
| P9 | 平台定位模糊 | S3-3 |
| P10 | 竞争分析未融入路线图决策 | S3-3 |

### DevOps 维度

| # | 问题 | 严重程度 | 行动编号 |
|---|------|---------|---------|
| D1 | CDK 未实际部署 | 阻塞级 | S4-2 |
| D2 | SQLite vs MySQL 测试差异 | 阻塞级 | S0-4 |
| D3 | CI/CD 不完整 | 重要 | S4-1 |
| D4 | MySQL vs PostgreSQL (RAG) | 重要 | S3-1 |
| D5 | 单 NAT Gateway 风险 | 建议 | S5 范围 |
| D6 | Secrets 管理不一致 | 重要 | S4-3 |
| D7 | 容器化零准备 | 阻塞级 | S0-3 |
| D8 | 监控告警缺失 | 重要 | S4-4 |
| D9 | 灾备目标激进 | 建议 | S3-3 |
| D10 | 多环境管理不完整 | 重要 | S4-2 |

### 性能维度

| # | 问题 | 严重程度 | 行动编号 |
|---|------|---------|---------|
| PERF1 | asyncio.to_thread 线程池瓶颈 | HIGH | S2-1 |
| PERF2 | SSE 长连接内存消耗 | MEDIUM-HIGH | S0-1 |
| PERF3 | 数据库连接池默认配置 | HIGH | S2-1 |
| PERF4 | 对话历史全量加载 | CRITICAL | S2-2 |
| PERF5 | Token 统计竞态条件 | MEDIUM | S5 范围 |
| PERF6 | OFFSET 分页性能 | MEDIUM | S5 范围 |
| PERF7 | ToolConfig NULL 列效率 | LOW-MEDIUM | 不处理 |
| PERF8 | 缓存层缺失 | HIGH | S2-4 |
| PERF9 | EventBus 内存泄漏 | HIGH | S2-3 |
| PERF10 | MySQL 向量搜索能力 | MEDIUM | S3-1 |
