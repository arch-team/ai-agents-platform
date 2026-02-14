# ADR-011: A2A 协议采纳评估 — 跨 Runtime Agent 通信策略

- **日期**: 2026-02-14
- **状态**: 已采纳
- **关联**: ADR-006 (Agent 框架选型), ADR-008 (Agent Teams 编排策略)

## 背景

### A2A 协议概述

A2A (Agent-to-Agent) 是 Google 主导、多厂商参与的开放协议标准，定义了 Agent 之间的发现、通信和任务委托机制。AgentCore Runtime 已原生支持 A2A 协议，提供以下核心能力：

- **Agent Card**: JSON 元数据端点 (`/.well-known/agent.json`)，描述 Agent 的名称、能力、技能、认证方式和端点 URL，使 Agent 可被发现和调用
- **Task 生命周期**: 定义 `submitted → working → input-required → completed/failed/canceled` 状态机，支持异步任务委托和进度追踪
- **消息传递**: 基于 JSON-RPC 2.0 的 `tasks/send` 和 `tasks/sendSubscribe` (SSE 流式) 方法，支持跨 Runtime 实例的 Agent 间通信
- **Artifact 交换**: 结构化输出物 (文件、数据、JSON) 在 Agent 间传递

### 当前 Multi-Agent 架构

项目通过 ADR-008 采纳了 Agent Teams 作为 Multi-Agent 编排策略，在 `execution` 模块内实现：

| 维度 | 当前实现 |
|------|---------|
| **编排模式** | Claude Agent SDK Teams 特性 (实验阶段) |
| **通信范围** | 单 Runtime 进程内，Teammate 间点对点消息 |
| **团队结构** | Agent 自主决定 (LLM 驱动)，TeamCreate/SendMessage/TaskCreate |
| **并发控制** | `asyncio.Semaphore(3)` + `max_turns=200` |
| **Token 消耗** | ~800K tokens/次 (3 人团队) |
| **数据模型** | `TeamExecution` + `TeamExecutionLog` 实体 |
| **API** | 6 个端点 (提交/列表/详情/日志/SSE流/取消) |

### AgentCore Runtime 部署状态

- 已部署: AgentCore Runtime (2 AZ) + Gateway (MCP 协议)
- 已完成: C-P3-4 (Agent 容器镜像构建 + ECR 推送) + C-P3-5 (调用路径切换)
- `AgentCoreRuntimeAdapter` 已实现 `IAgentRuntime` 接口，通过 `AGENT_RUNTIME_MODE` 配置切换执行路径
- Runtime 原生支持 A2A 协议，但平台侧尚未对接

### 决策驱动

1. `agentcore-integration-plan.md` P3-2 计划"通过 AgentCore Runtime A2A 协议支持跨会话 Agent 通信"
2. 竞品分析显示 AWS AgentCore、Azure AI Foundry、MS Agent Framework 均已支持 A2A
3. 路线图 §7.1 将"Multi-Agent 编排复杂度"标记为**高风险**，A2A 尚未经生产验证
4. M12 阶段需要明确 A2A 的采纳范围和优先级

## 备选方案

### 方案 A: 全面采纳 — Agent Card + 消息传递 + 任务编排

完整实现 A2A 协议全部能力，替代或补充当前 Agent Teams 机制。

| 优势 | 劣势 |
|------|------|
| 跨 Runtime 实例通信，突破单进程限制 | 开发量大 (~2000-3000 行)，涉及领域模型/API/适配器/前端 |
| 符合行业标准，未来互操作性好 | Agent Teams 和 A2A 双编排机制增加认知负担 |
| 支持异构 Agent 协作 (不同框架/模型) | A2A 协议尚在演进中，API 稳定性风险 |
| AgentCore 原生支持，无需自建传输层 | 当前 50 用户规模，跨 Runtime 需求尚未出现 |
| 可与外部平台的 Agent 互通 | 完整编排 (DAG/条件分支) 与 ADR-008 决策冲突 |

### 方案 B: 暂缓采纳 — 维持 Agent Teams 现状

不集成 A2A，继续使用 Agent Teams 单 Runtime 编排。

| 优势 | 劣势 |
|------|------|
| 零开发成本，专注 M12 其他交付 | 无法利用 AgentCore A2A 原生能力 |
| 当前编排机制已验证可用 | 未来跨 Runtime 需求出现时需从零开始 |
| 避免协议不稳定风险 | 与 agentcore-integration-plan P3-2 目标不一致 |
| 团队认知负担最低 | 缺少 Agent 发现机制，Agent 间互不可见 |

### 方案 C: 有限采纳 — Agent Card 注册 + 跨 Runtime 消息传递

分层采纳 A2A 核心能力，暂缓复杂编排协议。

| 优势 | 劣势 |
|------|------|
| 开发量适中 (~800-1200 行) | 不支持完整 A2A 任务编排 (DAG/条件/循环) |
| Agent Card 让 Agent 可被发现和描述 | 需要定义 Agent Card 与现有 Agent 实体的映射规则 |
| 跨 Runtime 消息为未来编排铺路 | 消息传递尚无明确业务场景驱动 |
| 与 Agent Teams 互补而非替代 | A2A 消息与 SDK SendMessage 两套通信机制 |
| 渐进增强，风险可控 | - |

## 决策

**选择方案 C: 有限采纳**，分两步实现 A2A 核心能力：

1. **Agent Card 注册与发现端点** — 实现
2. **跨 Runtime 异步消息传递** — 实现
3. **复杂编排协议 (DAG/条件分支/多轮协商)** — 暂缓，当前 Agent Teams 足够

## 方案对比

| 维度 | 方案 A: 全面采纳 | 方案 B: 暂缓 | 方案 C: 有限采纳 (决策) |
|------|:----------------:|:------------:|:----------------------:|
| **开发量** | ~2500 行 | 0 | ~1000 行 |
| **开发周期** | 3-4 周 | 0 | 1-2 周 |
| **Agent 可发现** | 是 | 否 | **是** |
| **跨 Runtime 通信** | 完整 | 否 | **基础消息** |
| **复杂编排** | 是 | 否 | 暂缓 |
| **与 Agent Teams 关系** | 补充+部分替代 | 无关 | **互补** |
| **协议稳定性风险** | 高 (依赖全协议) | 无 | **低** (仅核心子集) |
| **P3-2 目标达成** | 100% | 0% | **~70%** |
| **业务场景匹配** | 超前 | 不足 | **适中** |
| **认知负担** | 高 | 低 | 中 |

## 理由

### 1. Agent Card 是低成本高回报的能力补充

Agent Card 是一个 JSON 元数据端点，开发量小 (~200 行) 但价值显著：

- **Agent 可发现性**: 平台内所有 ACTIVE Agent 自动注册 Agent Card，通过标准端点暴露能力描述。其他 Agent (包括外部平台) 可通过 `/.well-known/agent.json` 发现并理解 Agent 的技能和调用方式
- **能力描述标准化**: Agent 的 system_prompt、工具列表、支持的模型等信息以 A2A Agent Card 标准格式发布，消除了"只有创建者知道这个 Agent 能做什么"的信息孤岛
- **与现有 `Agent` 实体天然映射**: `Agent.name` → `AgentCard.name`, `Agent.description` → `AgentCard.description`, `AgentConfig.tools` → `AgentCard.skills`, `AgentConfig.model_id` → `AgentCard.defaultInputModes`

```python
# Agent Card 映射示例
agent_card = {
    "name": agent.name,
    "description": agent.description,
    "url": f"{base_url}/api/v1/a2a/agents/{agent.id}",
    "version": "1.0.0",
    "capabilities": {
        "streaming": True,
        "pushNotifications": False,
    },
    "skills": [
        {"id": skill.name, "name": skill.name, "description": skill.description}
        for skill in agent_tools
    ],
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
}
```

### 2. 跨 Runtime 消息传递为未来扩展铺路

当前 Agent Teams 在单 Runtime 进程内工作良好，但存在天然上限：

| 限制 | 当前影响 | 未来影响 |
|------|---------|---------|
| 单进程内存 | 3 人团队 ~800K tokens 可接受 | 大团队或长任务可能 OOM |
| 单 Runtime 故障域 | Runtime 崩溃影响所有 Teammate | 不可接受 (生产环境) |
| 框架锁定 | 所有 Teammate 必须使用 Claude Agent SDK | 无法混合 Strands/其他框架 Agent |
| 水平扩展 | 无法跨 AZ 分布 Agent | 50+ 用户并发时可能成为瓶颈 |

跨 Runtime 消息传递通过 A2A `tasks/send` 方法解决这些限制。初期仅实现点对点异步消息，不引入复杂编排逻辑，保持与 Agent Teams 的正交关系：

- **Agent Teams**: 同 Runtime 内自主协作 (LLM 驱动)，适合探索性任务
- **A2A 消息**: 跨 Runtime 任务委托 (协议驱动)，适合确定性 Agent 间调用

### 3. 复杂编排暂缓的理由充分

ADR-008 已明确"Agent Teams 替代 DAG 引擎"的决策。A2A 协议的完整编排能力 (任务依赖图、条件分支、多轮协商) 与该决策存在重叠：

| 编排能力 | Agent Teams | A2A 全量 | 当前需求 |
|---------|:-----------:|:--------:|:--------:|
| 自主分工 | 是 | 否 (需预定义) | **需要** |
| 动态组团 | 是 | 否 (静态拓扑) | **需要** |
| 跨 Runtime | 否 | 是 | 暂不需要 |
| 确定性工作流 | 否 | 是 | 暂不需要 |
| 异构 Agent 协作 | 否 | 是 | 暂不需要 |

当前业务场景 (企业内部 AI Agent 平台，50 用户) 以探索性任务为主，Agent Teams 的 LLM 驱动自主编排更匹配需求。如未来出现跨团队/跨部门的确定性工作流需求，可在 A2A 消息传递基础上叠加编排层。

### 4. 渐进式采纳降低协议演进风险

A2A 协议仍在活跃演进中。有限采纳仅依赖协议的核心子集 (Agent Card + 消息传递)，这些是最稳定、最不可能变化的部分。复杂编排语义 (任务图、协商协议) 尚在讨论中，暂缓可避免被协议变更拖累。

## 影响

### 1. 新增领域模型: `AgentCard`

在 `agents` 模块 Domain 层新增 Agent Card 值对象，描述 Agent 的 A2A 元数据：

```python
# agents/domain/value_objects/agent_card.py
@dataclass(frozen=True)
class AgentCardSkill:
    """Agent Card 技能描述。"""
    id: str
    name: str
    description: str

@dataclass(frozen=True)
class AgentCard:
    """A2A Agent Card — Agent 的可发现元数据。"""
    name: str
    description: str
    url: str
    version: str
    skills: tuple[AgentCardSkill, ...]
    default_input_modes: tuple[str, ...] = ("text",)
    default_output_modes: tuple[str, ...] = ("text",)
    streaming: bool = True
    push_notifications: bool = False
```

**设计决策**: `AgentCard` 是 `Agent` 实体的派生视图，不独立持久化。通过 Application Service 从 `Agent` + `AgentConfig` + 工具列表实时构建。

### 2. 新增 API 端点

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/v1/agents/{id}/card` | GET | 获取单个 Agent 的 Agent Card | JWT (平台内部) |
| `/.well-known/agent.json` | GET | A2A 标准发现端点 (返回平台级 Agent 目录) | 可选 (根据部署策略) |
| `/api/v1/a2a/tasks/send` | POST | 跨 Runtime 发送消息给目标 Agent | JWT + Agent Card 验证 |
| `/api/v1/a2a/tasks/sendSubscribe` | POST | 跨 Runtime 流式消息 (SSE) | JWT + Agent Card 验证 |
| `/api/v1/a2a/tasks/{id}` | GET | 查询 A2A 任务状态 | JWT |

### 3. 新增适配器: `A2AMessageAdapter`

在 `execution/infrastructure/external/` 新增 A2A 消息传递适配器：

```python
# execution/infrastructure/external/a2a_message_adapter.py
class A2AMessageAdapter:
    """A2A 跨 Runtime 消息传递适配器。

    通过 AgentCore Runtime A2A API 向目标 Agent 发送任务消息。
    SDK-First: 薄封装层 < 100 行。
    """

    async def send_task(
        self,
        target_agent_url: str,
        message: str,
        *,
        session_id: str | None = None,
    ) -> A2ATaskResult: ...

    async def send_task_subscribe(
        self,
        target_agent_url: str,
        message: str,
    ) -> AsyncIterator[A2ATaskEvent]: ...

    async def get_task_status(self, task_id: str) -> A2ATaskStatus: ...
```

### 4. 对现有模块的影响

| 模块 | 影响程度 | 说明 |
|------|:--------:|------|
| `agents` | **低** | 新增 `AgentCard` 值对象 + Agent Card 构建逻辑 |
| `execution` | **中** | 新增 `A2AMessageAdapter` + A2A 任务端点；`TeamExecution` 无变更 |
| `shared` | **低** | 可能新增 `IA2AQuerier` 接口 (跨模块 Agent Card 查询) |
| `auth` | **无** | JWT 认证机制已足够 |
| `infra` | **低** | AgentCore Runtime 已支持 A2A，无 CDK 变更 |
| `frontend` | **低** | Agent 详情页展示 Agent Card 信息 (可选) |

### 5. 与 Agent Teams 的协作关系

```
同 Runtime 协作 (Agent Teams):
  User → TeamExecution API → ClaudeAgentAdapter (Teams mode)
       → SDK TeamCreate/SendMessage/TaskCreate → Teammates 自主协作
       → 结果写回 TeamExecution

跨 Runtime 委托 (A2A):
  User → A2A tasks/send API → A2AMessageAdapter
       → AgentCore Runtime A2A → 目标 Agent 的 Runtime
       → 目标 Agent 执行任务 → 返回结果

两者互补，不替代:
  Agent Teams = 同进程内 LLM 驱动的自主协作 (探索性任务)
  A2A 消息    = 跨进程的协议驱动任务委托 (确定性调用)
```

### 6. 实现顺序

| 步骤 | 内容 | 预估工期 | 依赖 |
|------|------|---------|------|
| 1 | `AgentCard` 值对象 + 构建逻辑 | 0.5 天 | - |
| 2 | Agent Card API 端点 (`/card` + `/.well-known/agent.json`) | 0.5 天 | 步骤 1 |
| 3 | `A2AMessageAdapter` 适配器 | 1 天 | - |
| 4 | A2A 任务 API 端点 (`tasks/send` + `tasks/sendSubscribe`) | 1 天 | 步骤 3 |
| 5 | 测试 (Agent Card 单元 + A2A 集成) | 1 天 | 步骤 1-4 |
| 6 | 前端 Agent Card 展示 (可选) | 0.5 天 | 步骤 2 |

## 风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|---------|
| A2A 协议规范变更 | 中 | 中 | 仅采纳核心子集 (Agent Card + 消息)，隔离层适配；关注 A2A 工作组更新 |
| AgentCore A2A API 不稳定 | 中 | 中 | `A2AMessageAdapter` 薄封装 + 降级路径 (回退到平台内部 HTTP 调用) |
| 跨 Runtime 网络延迟 | 低 | 低 | 异步消息 + SSE 流式；非实时场景优先 |
| Agent Card 信息泄露 | 低 | 中 | Agent Card 仅暴露公开元数据 (名称/描述/技能)，不包含 system_prompt 或内部配置；`/.well-known/agent.json` 端点可配置认证策略 |
| 与 Agent Teams 语义重叠导致用户困惑 | 中 | 低 | 前端明确区分: "团队协作" (Teams) vs "委托任务" (A2A)；API 文档说明使用场景 |
| Token 成本叠加 | 低 | 中 | A2A 消息本身不消耗 LLM Token (协议层通信)；仅目标 Agent 执行时产生 Token 消耗，成本归因到目标 Agent |

## 后续演进

| 演进方向 | 触发条件 | 预期方案 |
|---------|---------|---------|
| A2A 完整任务编排 | 出现跨团队/跨部门确定性工作流需求 | 在 A2A 消息基础上叠加 Task Graph 层 |
| Agent Card 注册中心 | Agent 数量 >50，跨平台发现需求 | 引入 Agent Registry 服务 |
| A2A 认证增强 | 对外暴露 Agent 服务 | A2A 协议层 OAuth 2.0 + mTLS |
| Strands Agent 互通 | ADR-013 评估后决策引入 Strands | A2A 作为异构框架 Agent 通信桥梁 |
| Agent Teams + A2A 融合 | Agent Teams 转正式特性 + A2A 编排成熟 | 统一编排层，Teams 处理同 Runtime，A2A 处理跨 Runtime |
