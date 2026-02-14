# ADR-013: Strands Agents SDK 战略评估 — 不迁移，保持观察

- **日期**: 2026-02-14
- **状态**: 已采纳
- **关联**: ADR-006 (Agent 框架选型), ADR-008 (Agent Teams 编排策略)

## 背景

### 当前技术选型

项目在 ADR-006 中选择 **Claude Agent SDK (claude-agent-sdk) 作为唯一 Agent 框架**，已深度集成到 `execution` 模块。当前集成现状：

- **SDK 版本**: claude-agent-sdk 0.1.35
- **集成代码**: 1500+ 行 SDK 集成代码 (ClaudeAgentAdapter + 工具构建 + Memory MCP + 消息解析)
- **测试覆盖**: 2085+ 测试 (含 Agent SDK 相关单元/集成测试)
- **Agent Teams**: 通过 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 环境变量启用，13+ 个 Teams 相关任务已完成 (ADR-008)
- **双路径架构**: `IAgentRuntime` 接口下 `ClaudeAgentAdapter` (主路径) + `AgentCoreRuntimeAdapter` (备选路径)
- **MCP 集成**: Gateway SSE + SDK 进程内 MCP Server + Memory MCP 三种模式

### Strands Agents SDK 出现

AWS 推出了 Strands Agents SDK，这是 AWS 官方开源的 Agent 框架，定位为 AgentCore 的原生开发工具。主要特点：

- **AWS 官方**: Apache 2.0 开源，AWS 维护
- **AgentCore 原生集成**: Identity、Memory、Observability 一等公民支持
- **多模型支持**: Claude、Titan、Llama、甚至 OpenAI 模型
- **纯 Python**: 无 Node.js 依赖
- **`@tool` 装饰器**: 直接定义工具函数，无需封装为 MCP Server
- **A2A 协议**: 原生支持 Agent-to-Agent 通信协议
- **结构化输出**: 内置 JSON Schema 约束
- **会话管理**: 内置长期记忆和会话状态管理

### 决策驱动

需要评估：是否应该从 Claude Agent SDK 迁移到 Strands Agents SDK？迁移的收益是否足以抵消已有投入的沉没成本和迁移风险？

## 备选方案

### 方案 A: 全面迁移到 Strands Agents SDK

将 `ClaudeAgentAdapter` 替换为基于 Strands SDK 的实现，移除 claude-agent-sdk 依赖。

| 优势 | 劣势 |
|------|------|
| AgentCore 原生集成，减少 MCP 桥接复杂度 | 废弃 1500+ 行已验证代码 |
| 纯 Python，移除 Node.js 运行时依赖 | 2085+ 测试需大面积重写 |
| 多模型支持，降低厂商锁定 | Agent Teams 功能需重新用 A2A 实现 |
| `@tool` 装饰器更 Pythonic | Strands SDK 为新发布，生产验证不足 |
| AWS 官方长期维护保障 | 迁移工期估计 4-6 周，Phase 4 时间紧张 |

### 方案 B: 不迁移，保持观察

维持 Claude Agent SDK 为唯一 Agent 框架，持续关注 Strands SDK 生态成熟度。

| 优势 | 劣势 |
|------|------|
| 零迁移成本，保护已有投入 | AgentCore 集成仍需 MCP 桥接 |
| 已验证的生产稳定性 | 仅支持 Claude 模型 |
| Agent Teams 功能已可用 | Node.js 运行时依赖持续存在 |
| IAgentRuntime 接口保障未来灵活性 | 可能错过 AWS 生态早期红利 |

### 方案 C: 渐进评估 — 新模块试点 Strands

在 Phase 5 中选择一个新增模块或独立场景用 Strands SDK 试点，积累经验后再决定是否全面迁移。

| 优势 | 劣势 |
|------|------|
| 低风险验证 Strands SDK 的生产能力 | 双框架共存增加认知负担 |
| 保留现有代码不变 | IAgentRuntime 需适配两套 SDK |
| 积累真实经验支撑后续决策 | 工具定义协议不一致 (MCP vs @tool) |
| 可随时回退，不影响主线 | 增加 CI/CD 和依赖管理复杂度 |

## 决策

**选择方案 B: 不迁移，保持观察**。维持 Claude Agent SDK 作为唯一 Agent 框架，利用 `IAgentRuntime` 接口抽象为未来可能的迁移保留通道。

## 方案对比

### 详细维度分析

| 维度 | Claude Agent SDK (当前) | Strands Agents SDK | 评估 |
|------|------------------------|-------------------|------|
| **1. AgentCore 集成深度** | 间接集成 — Gateway 通过 MCP SSE 连接，Memory 通过自定义 MCP Server 桥接，Observability 需独立集成 ADOT | 原生一等公民 — Identity/Memory/Observability 内置支持，SDK 自动对接 AgentCore 服务 | Strands 更优；但当前 MCP 桥接方案已验证可用 |
| **2. 模型支持范围** | 仅 Claude 系列 (Haiku/Sonnet/Opus)，通过 Bedrock Invoke API 调用 | 多模型 — Claude/Titan/Llama/Mistral/OpenAI，通过 Bedrock Converse API 或直连 | Strands 更优；但项目以 Claude 为核心 (ADR-010)，多模型需求低 |
| **3. 运行时依赖** | Python + Node.js 18+ (Claude Code CLI)，Docker 镜像增约 100MB | 纯 Python，无额外运行时，镜像更精简 | Strands 更优；Node.js 依赖是已知约束但不构成阻塞 (ADR-006 §6) |
| **4. 工具定义方式** | 统一 MCP 协议 — 自定义工具必须封装为 MCP Server (stdio/HTTP/SSE) | `@tool` 装饰器 — Python 函数直接注册为工具，更 Pythonic | Strands 更易用；但 MCP 统一协议与 AgentCore Gateway 设计理念一致 |
| **5. Multi-Agent 协作** | Agent Teams (实验性) — 通过环境变量启用，SDK 内置 TeamCreate/SendMessage/TaskCreate | A2A 协议 — 原生 Agent-to-Agent 通信，标准化协议 | 功能等价；Agent Teams 已集成并稳定运行 (83+ 测试) |
| **6. 内置工具集** | 13 种内置工具 (Read/Write/Edit/Bash/Glob/Grep/WebSearch/WebFetch/Task/NotebookEdit 等) | 无等价内置工具集，需自行封装或依赖第三方 | Claude Agent SDK 显著更优；内置工具集是核心差异化能力 |
| **7. 项目已有投入** | 1500+ 行集成代码，2085+ 测试，13+ Agent Teams 任务，生产验证中 | 零投入，从零开始 | 当前方案显著更优；沉没成本不可忽视 |
| **8. SDK 成熟度** | 0.1.35 版本，已有 AgentCore Runtime 生产部署案例 (BGL 金融合规) | 新发布，社区早期阶段，生产案例较少 | Claude Agent SDK 更优；Strands 需时间积累生产验证 |
| **9. 结构化输出** | 支持 — JSON Schema / Pydantic 验证 | 支持 — 内置结构化输出约束 | 功能等价 |
| **10. 会话管理** | resume/fork 机制 + MySQL 自建会话表 | 内置会话管理 + AgentCore Memory 原生对接 | Strands 更优；但当前会话管理已满足需求 |
| **11. 可观测性** | 无内置 — 需独立集成 ADOT SDK + CloudWatch (已完成) | AgentCore Observability 原生集成，自动 trace/metrics | Strands 更优；但独立 OTEL 方案已就位 (observability.md) |
| **12. 开源许可** | Anthropic 自有许可 (Anthropic API Terms) | Apache 2.0，标准开源许可 | Strands 更优；但对企业内部平台影响有限 |
| **13. 迁移成本** | 零 (现状) | 4-6 周全职工作，含代码重写 + 测试重写 + 集成验证 | 迁移成本高，Phase 4 时间线不允许 |
| **14. 架构灵活性** | IAgentRuntime 接口 + 双适配器 (ClaudeAgent + AgentCoreRuntime) | 需重新适配 IAgentRuntime 接口 | 当前架构已为未来迁移预留通道 |

### 综合评分

| 维度类别 | Claude Agent SDK | Strands SDK | 权重 |
|---------|:----------------:|:-----------:|:----:|
| **平台集成** (AgentCore/可观测性/会话) | 7/10 | 9/10 | 中 |
| **开发体验** (工具定义/运行时/许可) | 7/10 | 9/10 | 低 |
| **能力完整性** (内置工具/Multi-Agent/结构化) | 9/10 | 7/10 | 高 |
| **项目适配性** (已有投入/成熟度/迁移成本) | 10/10 | 3/10 | 高 |
| **加权总分** | **8.5/10** | **6.5/10** | - |

## 理由

### 1. 已有投入的保护价值远超迁移收益

当前 Claude Agent SDK 集成已深入项目核心：

```
已投入资产:
├── ClaudeAgentAdapter (316 行) — MCP 配置 + 工具构建 + Memory + SSRF 防护
├── AgentCoreRuntimeAdapter (120 行) — 备选路径
├── sdk_message_utils (消息解析)
├── memory_mcp_server (Memory MCP 桥接)
├── TeamExecution 领域模型 + 异步框架
├── 6 个 Team Execution API 端点
├── 2085+ 测试 (含大量 SDK 行为验证)
└── ADR-006 / ADR-008 / ADR-010 决策链
```

全面迁移意味着废弃上述全部资产，风险远大于 Strands SDK 在 AgentCore 集成上的边际改善。

### 2. IAgentRuntime 接口已提供迁移保险

ADR-006 的关键设计决策 — `IAgentRuntime` 抽象接口 — 使得框架切换成本可控：

```python
class IAgentRuntime(ABC):
    async def execute(self, request: AgentRequest) -> AgentResponseChunk: ...
    def execute_stream(self, request: AgentRequest) -> AsyncIterator[AgentResponseChunk]: ...
```

当前已有两个实现：
- `ClaudeAgentAdapter` — 主路径 (Claude Agent SDK)
- `AgentCoreRuntimeAdapter` — 备选路径 (boto3 invoke_inline_agent)

如果未来决定引入 Strands SDK，只需新增一个 `StrandsAgentAdapter`：

```python
class StrandsAgentAdapter(IAgentRuntime):
    """基于 Strands Agents SDK 的 Agent 运行时实现。"""
    async def execute(self, request: AgentRequest) -> AgentResponseChunk: ...
    def execute_stream(self, request: AgentRequest) -> AsyncIterator[AgentResponseChunk]: ...
```

通过依赖注入切换实现，上层 `ExecutionService` 和所有 API 端点无需任何修改。**接口抽象已将未来迁移成本从"全面重写"降低到"新增适配器"**。

### 3. Claude Agent SDK 的内置工具集是不可替代的差异化能力

Claude Agent SDK 内置 13 种工具 (Read/Write/Edit/Bash/Glob/Grep/WebSearch 等)，这些能力直接支撑了项目核心场景：

- **代码操作类 Agent**: 利用 Read/Write/Edit/Bash 完成代码审查和修改
- **研究类 Agent**: 利用 WebSearch/WebFetch 进行信息检索
- **协作类 Agent**: 利用 Task 工具实现子 Agent 分工

Strands SDK 不提供等价的内置工具集，迁移后这些能力需要自行封装或放弃。

### 4. Strands SDK 生产验证不足

Strands SDK 作为新发布的框架：

- 社区处于早期阶段，Issue/PR 反馈周期较长
- 缺少大规模生产部署案例
- API 可能存在 Breaking Changes 风险
- 文档和最佳实践尚在积累中

对比 Claude Agent SDK 已有 BGL 金融合规场景的 AgentCore Runtime 生产验证，稳定性差距明显。

### 5. Phase 4 时间线不允许大规模迁移

Phase 4 剩余任务 (M12 战略决策 + audit 增强 + insights 增强) 已排满。4-6 周的迁移工期将严重冲击交付计划。即使决定迁移，也应放在 Phase 5 执行。

## 迁移路径 (如果未来评估需要迁移)

虽然当前决策是不迁移，但需要明确：**如果 Strands SDK 在 6-12 个月内证明了生产可靠性且 AgentCore 深度集成带来显著收益，迁移路径如何执行**。

### 阶段 1: 评估与 POC (2 周)

```
任务:
├── 1.1 搭建 Strands SDK POC 环境
├── 1.2 实现 StrandsAgentAdapter (IAgentRuntime 接口)
├── 1.3 验证 AgentCore Identity/Memory/Observability 原生集成
├── 1.4 对比 Claude Agent SDK 在 3 个核心场景的表现
└── 1.5 编写评估报告 (ADR 更新)
```

### 阶段 2: 适配器开发 (2 周)

```
任务:
├── 2.1 实现 StrandsAgentAdapter (execute + execute_stream)
├── 2.2 工具映射: MCP 工具 → @tool 装饰器映射层
├── 2.3 Memory 集成: 从 MCP 桥接迁移到 Strands 原生 Memory
├── 2.4 Agent Teams 替代: 评估 A2A 协议实现
└── 2.5 单元测试 (新适配器 100% 覆盖)
```

### 阶段 3: 并行运行与验证 (1-2 周)

```
任务:
├── 3.1 通过 AgentConfig.runtime_type 配置切换
│     runtime_type: "claude_sdk" | "strands" | "basic"
├── 3.2 生产环境灰度: 10% 流量切到 StrandsAgentAdapter
├── 3.3 对比监控: 响应延迟、Token 消耗、错误率
└── 3.4 用户反馈收集
```

### 阶段 4: 全面切换 (1 周)

```
前提: 阶段 3 灰度验证通过 (错误率 < 0.1%, 延迟无回归)
任务:
├── 4.1 全量切换 runtime_type 默认值为 "strands"
├── 4.2 保留 ClaudeAgentAdapter 作为降级路径 (6 个月观察期)
├── 4.3 更新文档和 ADR
└── 4.4 6 个月后评估是否移除 claude-agent-sdk 依赖
```

### 迁移关键保障: IAgentRuntime 接口

```
当前架构:
ExecutionService
    └── IAgentRuntime (接口)
            ├── ClaudeAgentAdapter (主路径) ← claude-agent-sdk
            └── AgentCoreRuntimeAdapter (备选) ← boto3

迁移后架构:
ExecutionService
    └── IAgentRuntime (接口) ← 不变
            ├── StrandsAgentAdapter (主路径) ← strands-agents-sdk [新增]
            ├── ClaudeAgentAdapter (降级路径) ← claude-agent-sdk [保留]
            └── AgentCoreRuntimeAdapter (备选) ← boto3 [保留]
```

**核心保障**: `IAgentRuntime` 接口将框架差异封装在适配器层，上层业务逻辑 (ExecutionService、API 端点、TeamExecution) 完全不受影响。

## 影响

### 1. 无代码变更

本决策不涉及任何代码修改。现有 Claude Agent SDK 集成保持不变。

### 2. 观察清单

设立以下观察指标，在后续季度评审 (roadmap.md §8.3) 中定期检视：

| 观察维度 | 关注指标 | 触发重新评估的阈值 |
|---------|---------|:------------------:|
| **Strands SDK 成熟度** | GitHub Stars、Release 频率、Breaking Changes 数量 | Stars > 5K 且连续 3 个月无 Breaking Change |
| **生产验证** | AWS 官方案例数、社区生产部署报告 | >= 3 个同规模生产案例 |
| **AgentCore 集成收益** | Memory/Observability 自研桥接的维护成本 | 桥接代码维护成本 > 新增适配器成本 |
| **Claude Agent SDK 风险** | Node.js 依赖引发的运维问题、SDK 更新频率 | 连续 6 个月无更新或出现严重兼容性问题 |
| **多模型需求** | 业务方是否提出非 Claude 模型需求 | 有明确的多模型使用场景 |

### 3. Phase 5 排期预留

在 Phase 5 规划中预留 "Agent 框架重新评估" 窗口 (2 周)，届时基于观察清单的数据驱动决策。

### 4. 文档更新

ADR-006 状态保持"已采纳"不变，本 ADR 作为补充评估记录。

## 风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|---------|
| **Strands SDK 快速成熟，项目错过 AWS 生态早期红利** | 低 | 低 | Phase 5 重新评估窗口；IAgentRuntime 接口保障迁移成本可控 |
| **Claude Agent SDK 停止维护或重大 Breaking Change** | 低 | 高 | AgentCoreRuntimeAdapter 作为降级路径；IAgentRuntime 接口可快速切换到 Strands |
| **AgentCore 深度功能 (Identity/Memory) 仅面向 Strands SDK 优化** | 中 | 中 | 持续关注 AWS 文档和 re:Invent 发布；MCP 桥接方案已验证可行 |
| **Node.js 运行时依赖导致 Docker 镜像或安全扫描问题** | 低 | 低 | 多阶段构建已优化镜像大小；定期更新 Node.js 版本 |
| **Agent Teams 实验特性长期不转正** | 中 | 中 | 环境变量开关可随时关闭；A2A 协议 (Strands) 作为备选方案 |

## 附录: Strands SDK 代码示例 (仅供参考)

```python
# Strands Agents SDK 的典型用法 (如果未来迁移)
from strands import Agent, tool
from strands.models import BedrockModel

@tool
def search_knowledge(query: str) -> str:
    """搜索知识库。"""
    # 直接调用 Bedrock KB API
    return kb_client.retrieve(query)

agent = Agent(
    model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0"),
    tools=[search_knowledge],
    system_prompt="你是一个企业知识助手。",
)

response = agent("帮我查找最新的安全规范")
```

对比当前 Claude Agent SDK 用法：

```python
# Claude Agent SDK 当前用法
async for message in query(
    prompt="帮我查找最新的安全规范",
    options=ClaudeAgentOptions(
        system_prompt="你是一个企业知识助手。",
        model="us.anthropic.claude-sonnet-4-20250514-v1:0",
        mcp_servers={"gateway": {"type": "sse", "url": gateway_url}},
        allowed_tools=["mcp__gateway__search_knowledge"],
    ),
):
    yield extract_content(message)
```

两者在开发体验上的差异明显 (Strands 更 Pythonic)，但这不构成迁移的充分理由。
