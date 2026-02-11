# 项目学习总结：从 AI Agents Platform 中学到了什么

> **生成日期**: 2026-02-11
> **分析方式**: Claude Code Agent Teams 多维度并行分析（架构师 + 质量工程师 + 项目治理师 + 系统架构师）
> **项目状态**: M5 已完成，1,266 测试，95%+ 覆盖率，7 个已完成模块

---

## 项目概况速览

| 指标 | 数据 |
|------|------|
| 已完成模块 | 7 个 (shared, auth, agents, execution, tool-catalog, knowledge, insights) |
| 测试数量 | 1,266 个 |
| 覆盖率 | 95%+ |
| 规范文档 | 11 份 rules + 5 份 ADR |
| 变更积压 | 12/23 已完成 |
| 里程碑 | M1-M5 已完成，M6 待开始 |

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

**可借鉴的点**：架构合规测试让规范从"文档"变成"可执行断言"；薄封装原则强制抵抗过度抽象。

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

| 级别 | 定义 | 时间要求 | 当前进度 |
|------|------|---------|---------|
| S0 阻断修复 | 正确性缺陷或阻塞部署 | 进入 M5 之前 | 6/6 ✅ |
| S1 安全加固 | 高危安全漏洞 | M5 开发期间并行 | 2/5 |
| S2 性能解锁 | 并发瓶颈和资源泄漏 | M5 开发期间并行 | 3/4 |
| S3 战略决策 | 技术选型和产品方向 | M5 启动前决策 | 1/3 |
| S4 中期改进 | 架构优化和工程实践 | Phase 2 完成前 | 0/5 |

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

## 总结：五个可迁移的核心经验

| # | 经验 | 一句话解释 |
|---|------|-----------|
| 1 | 架构合规测试 | 把架构规范从文档变成 CI 中的可执行断言 |
| 2 | S0-S5 变更分级 | 战术性偿还技术债，而非无限期推迟或一次性清零 |
| 3 | 平台层/运行时层分离 | 资源管理和 AI 推理的关注点分离，独立演化 |
| 4 | progress.md 驱动器 | 结构化外部记忆让 AI 辅助开发具备跨会话连续性 |
| 5 | 规范即 Prompt | 将隐性工程知识显性化为 AI 可执行的结构化指令 |

这个项目的真正价值不在于技术栈选型，而在于**用严格的工程纪律证明了三件事**：

1. **DDD + Modular Monolith 可以在实践中落地** — 通过 R1-R5 隔离规则 + EventBus + 架构合规测试
2. **AI 可以成为可靠的长期协作伙伴** — 通过结构化规范 + 外部记忆 + 自动化质量门禁
3. **好的架构靠强制执行的规则持续守护** — 1,266 个测试和 95% 覆盖率是架构一致性的副产品，而非目标本身
