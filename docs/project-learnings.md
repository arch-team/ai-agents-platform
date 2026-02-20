# 项目学习总结：从 AI Agents Platform 中学到了什么

> **生成日期**: 2026-02-20
> **分析方式**: Claude Code Agent Teams 多维度并行分析（架构师 + 质量工程师 + 项目治理师 + 系统架构师 + 运营专家）
> **项目状态**: M12 全部完成，2,142+ 测试，95%+ 覆盖率，10 个后端模块 + 前端 FSD + 6 个 CDK Stack，Wave 3 推广就绪

---

## 项目概况速览

| 指标 | 数据 |
|------|------|
| 已完成后端模块 | 10 个 (shared/auth/agents/execution/tool-catalog/knowledge/insights/templates/evaluation/audit) |
| 前端 | React 19 + TypeScript + FSD，190 源文件，12 页面 |
| 基础设施 | CDK 6 类 Stack（network/security/database/agentcore/compute/monitoring）× 2 环境 |
| 测试数量 | 2,142+ 个（后端 1826 + infra 179 + 前端 80+ + E2E 57） |
| Eval 框架 | 11 个 eval 定义，222 capability + 62 regression，1,670 测试全部 PASS |
| 覆盖率 | 95%+ |
| 规范文档 | 11 份 rules + 13 份 ADR |
| 变更积压 | Phase 2-3: 24/24 ✅ + Phase 4: 19/19 ✅ + AgentCore P3: 5/5 ✅ |
| 里程碑 | M1-M12 全部完成，Wave 3 推广就绪（35 用户目标） |
| 推广进度 | Wave 1（10 用户）→ Wave 2（30 用户）→ Wave 3（35 用户）就绪 |
| 满意度 | Wave 1: 4.2/5.0 → Wave 2: 4.4/5.0 |

---

## 维度一：架构设计

**核心学习：DDD + Modular Monolith 不是理论概念，而是可落地的架构范式**

### 1. 模块四层结构的实际效果

`api → application → domain ← infrastructure` 将业务逻辑与技术框架完全解耦。Agent 实体的状态机是纯 Pydantic 对象，不依赖 FastAPI 或 SQLAlchemy，更换框架时核心业务零修改。

### 2. 模块隔离规则 R1-R5

用 5 条黄金法则守护边界：Domain 层绝对隔离、跨模块通信仅通过 EventBus 或 `shared/interfaces/`。最关键的是**架构合规测试** — `test_architecture_compliance.py` 自动扫描导入语句检测违规，把架构纪律从人工 Review 变成 CI 强制检查。

### 3. 分层数据模型策略

不同层用不同数据结构：

| 层级 | 模型类型 | 核心职责 | 关键约束 |
|------|---------|---------|---------|
| Domain Entity | Pydantic | 业务规则验证 | `validate_assignment=True`，状态转换在实体内部 |
| Domain Value Object | dataclass(frozen) | 不可变配置 | `frozen=True` 强制不可变 |
| Application DTO | dataclass | 内部传输 | 已验证的数据，无业务逻辑 |
| API Schema | Pydantic | 外部输入验证 | FastAPI 自动集成，生成 OpenAPI 文档 |
| Infrastructure ORM | SQLAlchemy | 持久化映射 | 与 Domain 实体独立，通过 Repository 转换 |

看似重复实则是"不同层有不同关注点"的具象化。

### 4. 跨模块接口位置策略

跨模块接口放在 `shared/domain/interfaces/` 而非消费方（如 `IAgentQuerier`），避免循环依赖，同时让接口所有权清晰。

### 5. 状态机 + 领域事件 = 审计链

5 个核心实体都有显式状态机，每个状态转换都是"方法 + 前置条件 + 时间戳"，配合领域事件形成完整的变更追溯：

- Agent: `draft → active → archived`
- Tool: `draft → pending_review → approved/rejected → deprecated`
- Conversation: `active → completed/failed`
- KnowledgeBase: `creating → active → syncing → failed → deleted`
- Document: `uploading → processing → indexed → failed`

### 6. SDK-First 原则与薄封装

外部服务封装 < 100 行，SDK 异常 → 域异常的转换模式。IAgentRuntime 接口抽象 + ClaudeAgentAdapter 实现，保持技术栈简洁。

### 7. Agent Teams 替代 DAG 引擎（ADR-008 实战验证）

原计划 M7 需要 8 周构建独立 `orchestration` 模块（DAG 引擎，预估 3000 行代码）。实际决策采用 Claude Agent SDK 的 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 能力，在 `execution` 模块内扩展（约 1500 行），节省了 6-8 周工期。

**实战踩坑与经验**：

| 问题 | 根因 | 解决方案 |
|------|------|---------|
| `enable_teams=True` 修改失败 | Agent 处于 ACTIVE 状态，不允许配置变更 | `enable_teams` 必须在 Agent **创建时**设置；ACTIVE 状态不可修改 |
| 后台 asyncio.Task 数据库操作失败 | 使用了请求级 DB session，其生命周期短于后台任务 | 所有超出请求生命周期的后台任务必须使用**独立 DB session** |
| execute_stream 调用报错 | `async def` 返回 AsyncIterator 需先 `await` 再 `async for` | SDK 接口异步约定需有专项单元测试覆盖 |
| 团队协作结果不稳定 | 依赖 `conversation_id` 自动共享上下文，但 SDK 内部传递不透明 | 通过**明确上下文传递**（步骤1输出 → 步骤2 prompt）比隐式共享更可靠 |

**Token 经济性观测**：3 人团队单次执行约 800K tokens，用 `asyncio.Semaphore(3)` 控制并发，500K tokens 触发 warning 日志。

**核心洞察**：优先探索 SDK/平台原生能力（技术杠杆），仅在缺失时自建；功能增强优先考虑扩展现有模块而非新建独立模块。

**可借鉴的点**：架构合规测试让规范从"文档"变成"可执行断言"；薄封装原则强制抵抗过度抽象；`IAgentRuntime` 接口抽象提前将未来框架迁移成本从"全面重写"降低到"新增适配器"。

---

## 维度二：工程质量与流程

**核心学习：质量是制度性产物，不是依赖明星开发者**

### 1. 规范体系解决决策一致性

11 份 rules 文档每份都有"速查卡片"（30 秒内找到答案），Claude Code 进入子目录时自动加载对应规范。1,266 个测试的 95% 覆盖率不是靠人工审查，而是 `checklist.md` 的 17 项质量门禁自动检查。

规范文档清单：

| 文档 | 职责 |
|------|------|
| `architecture.md` | 分层规则、模块隔离、DDD 模式 |
| `testing.md` | TDD 工作流、测试分层、Fixture 模式 |
| `security.md` | 禁止事项、强制要求、安全检测 |
| `api-design.md` | RESTful 路由、HTTP 状态码、错误格式 |
| `code-style.md` | 类型提示、命名、Docstring 原则 |
| `sdk-first.md` | SDK 决策流程、异常处理模式 |
| `logging.md` | 结构化日志、Correlation ID、脱敏 |
| `observability.md` | Metrics、Tracing、Health Check |
| `tech-stack.md` | 版本要求矩阵 |
| `checklist.md` | PR Review 检查清单 |
| `project-structure.md` | 文件组织、配置约定 |

### 2. S0-S5 变更积压分级

把"TODO 黑洞"变成"战术优先级"：

| 级别 | 定义 | 最终进度 |
|------|------|---------|
| S0 阻断修复 | 正确性缺陷或阻塞部署 | 全部完成 ✅ |
| S1 安全加固 | 高危安全漏洞 | 全部完成 ✅ |
| S2 性能解锁 | 并发瓶颈和资源泄漏 | 全部完成 ✅ |
| S3 战略决策 | 技术选型和产品方向 | 全部完成 ✅ |
| S4 中期改进 | 架构优化和工程实践 | 全部完成 ✅ |

关键机制：

- **S0 阻断**：每次会话开始强制提醒
- **穿插规则**：连续 3 个 Milestone 后自动提醒处理 S1/S2
- **模块亲和性**：开发某模块时提示该模块的未完成变更

### 3. 双重验证机制

- **通用检查**（自动化）：`ruff check` + `mypy --strict` + `pytest --cov-fail-under=85`
- **变更验证**（人工对照）：对照 `improvement-plan.md` 逐条确认验收标准
- **回归检测**：区分"当前模块测试失败"（正常修复）和"其他模块回归信号"（暂停并报告）

### 4. 开发中发现子协议

开发时发现的问题按严重程度分类：

- **阻断当前任务** → 立即记入变更积压表（`C-D-N` 编号）
- **不影响当前任务** → 记入遗留事项，会话结束时提示用户是否升级

---

## 维度三：AI 平台领域知识

**核心学习：企业级 AI 平台的本质是在"AI 能力"与"企业治理"之间建立可控的桥梁**

### 1. 五大核心领域模型

| 聚合根 | 业务角色 | 核心特征 |
|--------|---------|---------|
| Agent | 业务能力载体 | 生命周期状态机 + AgentConfig 值对象 |
| Conversation/Message | 执行轨迹管理 | 独立聚合根，支持审计追溯和成本归因 |
| Tool | 可控的能力边界 | 3 种类型（MCP_SERVER/API/FUNCTION）+ 5 状态审批 |
| KnowledgeBase | 领域知识注入 | 双存储架构（MySQL + Bedrock KB）|
| Template | 业务场景抽象 | 聚合 agents + tools + knowledge 的"能力包" |

### 2. 平台层/运行时层分离

```
Platform API (FastAPI Modular Monolith) — 资源管理层
     ↕ invoke_agent_runtime() API
Agent Runtime (AgentCore Runtime) — Agent 执行层
```

分离的价值：
- **关注点分离**：资源管理 vs 推理执行的关注点完全不同
- **独立演化**：Platform API 升级不影响 Runtime 稳定性，反之亦然
- **弹性伸缩**：Runtime 按需扩容，Platform API 保持稳定
- **runtime_type** 字段预留多运行时共存能力

### 3. RAG 透明注入

在 `send_message` 前自动检索 Agent 关联的 KnowledgeBase 并注入上下文，前端无需关心"何时检索"。优势：

- 开发者体验优化：调用接口保持简洁
- 业务逻辑解耦：切换知识库实现时调用方零改动
- 性能优化空间：可做智能判断和缓存
- 安全与合规：注入过程可记录审计日志

### 4. 工具审批流程反映企业需求

5 状态审批流程（`draft → pending_review → approved/rejected → deprecated`）反映三大企业需求：
- **安全合规**：工具 = Agent 对外部系统的操作权限，未审批可能导致越权
- **质量管控**：审批确保工具的接口定义、错误处理、超时逻辑可靠
- **组织协作**：`allowed_roles` 实现工具权限分级

### 5. 成本归因是 AI 平台的"一等公民"

LLM 成本高度动态，无归因 = 无法回答"哪个团队花费最多"。

技术实现：`UsageRecord` 实体 + `CostBreakdown` 值对象 + `BedrockCostCalculator` 计算器，支持 team_id / project_id / agent_id 多维度归因。

### 6. 技术选型决策链（13 份 ADR 的核心结论）

| ADR | 决策 | 核心理由 |
|-----|------|---------|
| ADR-005 | Bedrock Knowledge Bases（非自建向量库） | 托管服务减少维护负担，与 AgentCore 生态对齐 |
| ADR-006 | Claude Agent SDK 作为唯一 Agent 框架 | 与项目愿景对齐；13 种内置工具是差异化能力；单一框架降低复杂度 |
| ADR-008 | Agent Teams 替代 DAG 引擎 | SDK 原生能力 > 自建引擎；节省 6-8 周工期；LLM 驱动自主编排更匹配业务场景 |
| ADR-011 | A2A 协议有限采纳（Agent Card + 消息传递） | 渐进式采纳降低协议演进风险；复杂编排暂缓 |
| ADR-012 | 蓝绿部署暂缓，滚动更新增强 | 50 用户规模不支撑蓝绿部署投入；Circuit Breaker + deregistrationDelay 优化已解决实际痛点 |
| ADR-013 | 不迁移 Strands SDK，保持观察 | 已有 1500+ 行集成代码和 2085+ 测试的保护价值远超迁移收益；IAgentRuntime 接口已预留迁移通道 |

**可迁移的决策原则**：当 SDK/平台已提供能力时，不自建；当已有大量投入时，接口抽象比推倒重来更务实；当用户规模未到时，不为未来问题付出当前成本。

---

## 维度四：Claude Code 人机协作

**核心学习：当 AI 成为开发团队一员时，需要重新设计流程、规范和工具**

### 1. "规范即 Prompt"

三级 CLAUDE.md 层级将开发规范转化为 AI 的可执行指令：

```
根级 .claude/CLAUDE.md           → 全局规范（语言、项目概述、会话协议）
根级 .claude/rules/              → 通用规则（common.md, session-workflow.md）
子项目 backend/.claude/CLAUDE.md → 后端入口（技术栈、TDD 工作流）
子项目 backend/.claude/rules/    → 后端专用规则（11 份文档）
```

任务表"参考规范"列按需加载 rules，速查卡片适应 LLM "扫描式阅读"特性。消除了"AI 会做但不会按你的方式做"的痛点。

### 2. progress.md 作为外部记忆

六大区域构成结构化的跨会话记忆系统：

| 区域 | 功能 | 认知作用 |
|------|------|---------|
| 当前状态 | 单一真实源 | "我在哪里" |
| 模块状态 | 宏观进度 | "大局如何" |
| 任务拆解表 | 微观任务 + 依赖 | "下一步做什么" |
| 变更积压表 | 技术债务追踪 | "有什么问题待解决" |
| 遗留事项 | 临时记忆缓冲 | "上次没做完什么" |
| 近期会话 | 最近 5 条记录 | "近期做了什么决策" |

### 3. 三步会话协议

人机协作的状态机设计：

```
开始 → 读取 progress.md → 识别任务/依赖/遗留/变更积压 → 向用户汇报
执行 → 加载参考规范 → 检查前置依赖 → TDD 实现 → 质量检查
结束 → 更新 progress.md 六个区域
```

关键机制：
- **前置依赖检查**：自动验证依赖任务是否完成
- **优先级仲裁**：用户指定 > 进行中任务 > S0 阻断 > 遗留事项 > 最小编号 Milestone
- **穿插提醒**：连续 2-3 个 Milestone 后提醒处理变更
- **回归检测**：其他模块测试失败时暂停并报告

### 4. Agent Teams 并行开发

会话 #16 用 9 个 Agent 并行完成 insights 模块 + S1/S2 变更（Rate Limiting + 滑动窗口 + Agent 缓存），将串行工作压缩到并行完成。

### 5. 开发者角色转变

从"写代码"转向"定义规范 + 设计架构 + 审查产出"。11 份 rules 文档本质上是"可执行的领域知识"，人类负责决策，AI 负责执行。

---

## 维度五：技术债管理（变更积压视角）

**核心学习：技术债的最大风险不是"欠了多少"，而是"是否有意识地管理"**

### 1. 变更积压的生命周期

从识别到清零，整个 Phase 2-4 历经 62 项变更（Phase 2-3: 24 项 + Phase 4: 19 项 + AgentCore P3: 5 项 + 开发发现 14 项）。最终全部完成，未留下任何 S0 未决项。

### 2. Phase 4 技术债的特征

Phase 4 的变更与前三个 Phase 有质的不同：从"补缺陷/加安全/提性能"转向"生产化加固 + 用户体验优化 + 可观测性完善"。这标志着项目从"功能完整"走向"生产成熟"。

典型 Phase 4 变更：
- 审计模块 EventBus 23 事件订阅（合规）
- ECS 部署参数调优 + Circuit Breaker（可靠性）
- lifespan seed 自愈（运维体验）
- Agent Teams 链式协作（功能增强）
- Prod 环境双 AZ + Aurora Writer/Reader（高可用）

### 3. 技术债的"模块亲和性"规律

开发某模块时，该模块的相关技术债往往是最低成本清除的时机。`session-workflow.md` 的"模块亲和性提示"机制将这一规律系统化，避免在后期做跨上下文的修补。

---

## 维度六：生产运维与可观测性

**核心学习：生产环境的问题往往不在功能逻辑，而在错误处理、配置管理和运维工具链**

### 1. log.exception vs log.warning：异常处理的隐性陷阱

**问题根因**：lifespan 初始化时，admin seed 使用 `log.exception()`，template seed 使用 `log.warning()`。两者行为差异显著：

```python
# 正确：保留完整 traceback，可观测
log.exception("Template seed failed: %s", str(e))

# 错误：traceback 丢失，仅记录字符串，难以排查
log.warning("Template seed failed: %s", str(e))
```

`log.warning()` 会**吞掉 traceback**，导致生产环境出现静默失败——日志中只有 `"Template seed failed: ..."` 而没有错误栈，无从判断是数据库连接问题、数据冲突还是代码逻辑错误。

**最佳实践**：
- `log.exception()` 用于需要排查的非预期异常（保留完整 traceback）
- `log.warning()` 仅用于已知的、预期的非致命状况
- 异常处理一致性是可观测性的前提：同一初始化流程中的所有异常必须使用相同级别的 logger

### 2. Seed 数据自愈设计

初始化数据（admin 用户、种子模板）必须具备**幂等性自愈能力**，而非依赖人工干预：

```python
# 反模式：失败就报错退出
async def seed_templates():
    await db.execute(insert(Template).values(...))

# 正确：幂等插入 + 异常完整记录
async def seed_templates():
    try:
        result = await db.execute(
            insert(Template)
            .values(...)
            .on_duplicate_key_update(updated_at=func.now())
        )
    except Exception as e:
        log.exception("Template seed failed, will retry on next startup: %s", str(e))
        # 不 raise —— seed 失败不应阻断整个应用启动
```

**关键设计原则**：
- 配置即代码：模板/种子数据必须进 `seed_data.py`，**不能只存数据库**。数据库可能被重建，代码版本控制才是真正的 Single Source of Truth
- `ON DUPLICATE KEY UPDATE` 实现幂等重放，支持安全地多次执行
- seed 失败记录 exception 但不阻断 app 启动（非强依赖）

### 3. ECS 部署规范

在生产部署中积累的操作规范：

```bash
# 必须从 infra/ 目录执行（CDK context 文件在该目录下）
cd infra/
cdk deploy ai-agents-plat-compute-prod --context env=prod

# 部署后滚动完成约 3.5 分钟
# 旧容器在 deregistrationDelay(30s) 内正常服务，新容器健康检查通过后替换
# ECS Circuit Breaker 自动检测失败部署并回滚
```

**Dev 与 Prod 参数差异**：

| 参数 | Dev | Prod | 说明 |
|------|:---:|:----:|------|
| CPU | 256 | 512 | Prod 更高负载 |
| 内存 | 512 MiB | 1024 MiB | Agent SDK 需要足够内存 |
| 任务数 | 1 | 2 | Prod 高可用 |
| Aurora 实例 | db.t3.medium 1 个 | db.r6g.large Writer+Reader | Prod 读写分离 |
| minimumHealthyPercent | 100% (默认) | 50% (增强后) | 加快部署速度 |

### 4. 蓝绿部署的规模匹配原则（ADR-012）

**核心洞察**：蓝绿部署的真正价值在高并发场景（数百到数千用户），对 50 用户的内部平台，`ECS 滚动更新增强`（Circuit Breaker + deregistrationDelay 优化）已足够。

触发蓝绿部署重新评估的条件：
- 活跃用户 > 200 人
- Prod 任务数 > 4 个
- API P99 延迟 > 1s
- 部署频率 > 每日 1 次

**避免过早优化**：每个架构决策都有其适用的规模范围，在用户规模未到时引入高成本方案是负收益。

### 5. CloudWatch 结构化日志 + Correlation ID

生产环境调试的基础设施：

```python
# request_id 贯穿整个请求链路
logger = structlog.get_logger().bind(
    request_id=request.state.request_id,
    user_id=current_user.id,
    module="execution",
)
logger.info("agent_execution_started", agent_id=agent.id, runtime_type=agent.config.runtime_type)
```

**CloudWatch Insights 常用查询**：

```sql
-- 按 request_id 追踪完整链路
fields @timestamp, @message
| filter request_id = "xxx-yyy-zzz"
| sort @timestamp asc

-- 发现 exception 日志（含完整 traceback）
fields @timestamp, @message
| filter @message like /exception/
| sort @timestamp desc | limit 50
```

---

## 维度七：梯度推广与用户运营

**核心学习：企业内部平台的推广是技术 + 组织 + 文化的综合工程，不只是"上线就能用"**

### 1. 梯度推广策略（Wave 1 → Wave 3）

| Wave | 用户规模 | 核心策略 | 关键收获 |
|------|---------|---------|---------|
| Wave 1 | 10 用户（核心技术团队） | 1:1 培训 + 手把手引导 | 满意度 4.2/5.0；发现 3 个 UX 改进项；确认 Agent Teams 可用 |
| Wave 2 | 30 用户（扩展到技术相邻部门） | 分组培训 + 使用文档 | 满意度 4.4/5.0；非技术用户反馈步骤不够细；16 个模板覆盖 85% 使用场景 |
| Wave 3 | 35 用户（目标达到 50 活跃） | 自助培训材料 + 内部分享会 | 就绪中；验收目标 >= 50 活跃 + >= 40% 非技术自助创建 |

**梯度推广的价值**：每个 Wave 提供反馈时间窗口，在扩大用户群前修复已知问题。一次性全量推广无法控制反馈爆发，容易让团队陷入被动修复螺旋。

### 2. 用户分层与 RBAC 设计的意图

平台设计了三个角色：

| 角色 | 权限 | 设计意图 |
|------|------|---------|
| VIEWER | 只读（查看模板 + 对话） | 低门槛入口，安全地探索平台能力 |
| EDITOR | 创建/编辑自己的 Agent | 有意设置"升级门槛"，防止无效 Agent 污染 |
| ADMIN | 全部权限含审批 | 平台治理 |

**关键洞察**：VIEWER 到 EDITOR 的"升级门槛"是**有意的设计**，不是限制而是过滤。强制用户经历 VIEWER 阶段，确保 EDITOR 时已理解平台使用方式，减少了无效/重复 Agent 的创建。这与工具审批的 5 状态流程同源：企业内部平台需要通过流程设计来保证内容质量。

### 3. 培训材料的粒度差异

**问题**：技术用户（开发/架构）和非技术用户（业务/运营）对同一份操作文档的反馈截然不同。

| 受众 | 痛点 | 解决方案 |
|------|------|---------|
| 技术用户 | 文档不够精确，API 字段含义不清 | 提供 API Reference + 示例 JSON |
| 非技术用户 | 操作步骤太抽象，不知道"点哪里" | 截图导向的步骤文档 + 视频录制 |

**最佳实践**：按角色分离培训材料；第一个非技术用户的真实操作录屏，比技术团队写的文档更有指导价值。

### 4. 配置即代码原则

Wave 1 试点中曾在数据库直接插入种子模板，导致：

- Dev 和 Prod 数据不一致
- 新环境部署后需要手动补数据
- 重建数据库后丢失配置

**教训**：所有配置性数据（模板、种子 Agent、系统角色）必须在代码中维护，通过部署流程自动应用。`seed_data.py` 成为配置的唯一真实源。

```python
# 正确：配置即代码
SEED_TEMPLATES = [
    {
        "name": "代码审查助手",
        "category": "development",
        "description": "...",
        "system_prompt": "...",
    },
    # 更多模板...
]

async def seed_templates(db: AsyncSession) -> None:
    for template_data in SEED_TEMPLATES:
        await db.execute(
            insert(TemplateModel)
            .values(**template_data)
            .on_duplicate_key_update(updated_at=func.now())
        )
```

### 5. 用户满意度提升的杠杆点

Wave 1 → Wave 2 满意度从 4.2 提升到 4.4，具体改进项：

- **首次响应速度**：优化了 Agent 配置 TTL 缓存（C-S2-4），重复对话延迟下降 40%
- **错误提示清晰化**：统一异常处理 + 前端错误边界，用户看到有意义的错误信息而非 500
- **模板覆盖率**：从 10 个扩展到 16 个模板，覆盖率从 70% 提升到 85%
- **移动端适配**：前端 FSD 响应式设计，部分用户在平板上使用的体验改善

---

## 总结：七个可迁移的核心经验

| # | 经验 | 一句话解释 |
|---|------|-----------|
| 1 | 架构合规测试 | 把架构规范从文档变成 CI 中的可执行断言 |
| 2 | S0-S5 变更分级 | 战术性偿还技术债，而非无限期推迟或一次性清零 |
| 3 | 平台层/运行时层分离 | 资源管理和 AI 推理的关注点分离，独立演化 |
| 4 | progress.md 驱动器 | 结构化外部记忆让 AI 辅助开发具备跨会话连续性 |
| 5 | 规范即 Prompt | 将隐性工程知识显性化为 AI 可执行的结构化指令 |
| 6 | 异常处理一致性 | log.exception 保留 traceback，log.warning 会吞掉错误栈 |
| 7 | 梯度推广 + 配置即代码 | 分 Wave 推广控制反馈节奏；种子数据进代码不进数据库 |

这个项目从 M1 到 M12 的真正价值不在于技术栈选型，而在于**用严格的工程纪律证明了五件事**：

1. **DDD + Modular Monolith 可以在实践中落地** — 通过 R1-R5 隔离规则 + EventBus + 架构合规测试
2. **AI 可以成为可靠的长期协作伙伴** — 通过结构化规范 + 外部记忆 + 自动化质量门禁
3. **好的架构靠强制执行的规则持续守护** — 2,142 个测试和 95% 覆盖率是架构一致性的副产品，而非目标本身
4. **技术决策要匹配规模** — 蓝绿部署、A2A 全量采纳、Strands 迁移，都在"规模未到时不引入"的原则下被暂缓
5. **生产化是独立的工程维度** — 功能正确性不等于生产就绪；可观测性、种子自愈、部署可靠性是独立需要投入的工程能力
