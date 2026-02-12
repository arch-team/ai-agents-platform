# ADR-008: Agent Teams 替代 DAG 引擎 — Multi-Agent 编排策略选型

- **日期**: 2026-02-12
- **状态**: 已采纳
- **关联**: ADR-006 (Agent 框架选型), ADR-007 (Phase 3 路线图调整)

## 背景

### 原 M7 规划

roadmap.md Phase 3 计划 M7 (第 29-36 周) 实现 `orchestration` 独立模块：

- DAG 定义引擎（Workflow + Node + Edge 实体）
- 执行引擎（拓扑排序 + 并行调度 + 状态追踪）
- Agent 间消息路由
- 前端可视化 DAG 编辑器

预估复杂度高，roadmap.md §7.1 已将"Multi-Agent 编排复杂度"标记为**高风险**。

### Claude Code Agent Teams 能力

Claude Agent SDK 通过环境变量 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 启用 Agent Teams 能力，Agent 自动获得 TeamCreate / SendMessage / TaskCreate 等工具，可以：

- 自主决定团队结构（人数、角色分工）
- 动态分配和追踪任务
- Teammate 间点对点消息传递
- 团队级 Task List 协调

## 决策

**采用 Agent Teams 能力替代自建 DAG 引擎**，在 `execution` 模块内扩展实现，不引入独立 `orchestration` 模块。

## 方案对比

| 维度 | 方案 A: DAG 引擎 (原规划) | 方案 B: Agent Teams (采纳) |
|------|--------------------------|--------------------------|
| **编排模式** | 显式预定义 (用户画 DAG) | Agent 自主编排 (LLM 决定) |
| **灵活性** | 低 — 固定拓扑 | 高 — 动态组团、动态分工 |
| **新增代码量** | ~3000 行 (Workflow/Node/Edge/Executor) | ~1500 行 (TeamExecution + API) |
| **新模块** | `orchestration` 独立模块 | 在 `execution` 模块内扩展 |
| **前端配套** | 重 — 可视化 DAG 编辑器 | 轻 — 提交任务 + 查看进度 |
| **外部依赖** | 无 (自建) | Claude Agent SDK Teams 特性 |
| **适用场景** | 固定流程、合规审批链 | 研究探索、代码审查、复杂分析 |
| **Token 消耗** | 可预测 (固定节点数) | 较高 (~800K/3 人团队) |
| **开发周期** | 8 周 (含前端) | 已完成 (后端 7 Phase) |

## 理由

1. **业务场景匹配**: 企业内部 AI Agent 平台的核心场景是"让 Agent 自主完成复杂任务"，而非"运行预定义工作流"。Agent Teams 更匹配这一需求。

2. **技术杠杆**: Claude Code 的 Teams 能力已实现了团队创建、任务分配、消息协调等核心编排逻辑。自建 DAG 引擎是在重复造轮子。

3. **复杂度控制**: DAG 引擎涉及拓扑排序、死锁检测、并行调度、失败回退等复杂逻辑，是 roadmap 中标记的高风险项。Agent Teams 将这些复杂度委托给 SDK。

4. **前端成本**: DAG 编辑器是前端重度投入项 (拖拽画布 + 节点连线 + 实时验证)。Agent Teams 只需轻量的任务提交和进度查看界面。

5. **渐进增强**: 如果未来确实出现"固定工作流"的强需求，可以在 Agent Teams 基础上叠加 Workflow 概念，而非推翻重建。

## 风险与缓解

| 风险 | 概率 | 缓解措施 |
|------|:----:|---------|
| Agent Teams 特性处于实验阶段 | 中 | 环境变量开关，可随时回退到单 Agent 模式 |
| Token 消耗高 (~800K/团队) | 高 | max_turns=200 间接控制；asyncio.Semaphore(3) 并发限制；后续可增加 Token 预算参数 |
| 不支持确定性工作流 | 低 | 当前业务场景以探索性任务为主；如需确定性流程，可后续叠加 Workflow 层 |
| 长时间异步执行 (分钟级) | 中 | TeamExecution 实体 + 异步 API + SSE 进度推送已解决 |

## 实现概要

在 `execution` 模块内扩展，新增:

- **配置层**: `AgentConfig.enable_teams` 布尔开关
- **运行时**: `ClaudeAgentAdapter` 注入 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 环境变量
- **领域模型**: `TeamExecution` 实体 (状态机: PENDING → RUNNING → COMPLETED/FAILED/CANCELLED) + `TeamExecutionLog` 日志
- **异步执行**: `TeamExecutionService` 基于 `asyncio.Task` 后台执行 + `asyncio.Semaphore(3)` 并发控制
- **API**: 5 个端点 (`POST /team-executions`, `GET` 列表/详情, `GET /stream` SSE, `POST /cancel`)
- **测试**: 79 个新测试，全部通过

## 后续演进

- **Phase 3 M8**: 团队执行结果纳入 evaluation 模块的自动化评估
- **Phase 4**: 如出现固定工作流需求，可在 TeamExecution 基础上新增 WorkflowTemplate 概念
- **SDK 升级**: 当 Agent Teams 从实验特性转为正式特性后，移除环境变量开关
