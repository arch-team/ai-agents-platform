# AI Agents Platform - 产品架构蓝图

> **文档定位**: 产品级架构蓝图，建立能力模块与技术实现之间的映射关系。
>
> **目标读者**: 技术负责人、架构师、核心开发者
>
> **相关规范**: 后端 [backend/.claude/rules/architecture.md]、前端 [frontend/.claude/rules/architecture.md]、基础设施 [infra/.claude/rules/architecture.md]

---

## 1. 产品能力总览

AI Agents Platform 是基于 Amazon Bedrock AgentCore 的企业内部 AI Agents 平台，为组织提供 Agent 全生命周期管理、多 Agent 编排协作、运行监控与质量评估等核心能力。

**平台核心价值**:

- **统一管理**: 集中管理企业内部所有 AI Agent 的创建、配置、部署和版本迭代
- **编排协作**: 支持多 Agent 工作流编排，实现复杂业务场景的自动化
- **可观测性**: 提供完整的执行监控、性能追踪、成本核算和质量评估体系
- **安全合规**: 基于 RBAC 的权限控制和资源隔离，满足企业级安全要求
- **扩展性**: 插件化工具集成和多模型支持，适应不同业务场景需求

**能力架构概览**:

```
┌──────────────────────────────────────────────────────────────────┐
│                     AI Agents Platform                           │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│  Agent   │  运行时  │  编排    │  监控    │  用户    │  平台    │
│  管理    │  引擎    │  协作    │  评估    │  权限    │  基础    │
├──────────┴──────────┴──────────┴──────────┴──────────┴──────────┤
│              Amazon Bedrock AgentCore + Claude SDK               │
├─────────────────────────────────────────────────────────────────┤
│                    AWS 基础设施 (CDK)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 六大核心能力模块

### 2.1 Agent 管理 -- Agent 全生命周期管理

负责 Agent 从创建到退役的完整生命周期，包括配置管理、版本控制和模板复用。

**子能力**:

| 子能力 | 说明 | 关键实体 |
|--------|------|---------|
| Agent 创建/配置 | 定义 Agent 的基础信息、模型选择、系统提示词和参数配置 | `Agent`, `AgentConfig` |
| 版本管理 | Agent 配置的版本快照，支持回滚和灰度发布 | `AgentVersion` |
| Agent 模板市场 | 预置和用户自定义的 Agent 模板，降低创建门槛 | `AgentTemplate` |
| 提示词管理 | 系统提示词和用户提示词的集中管理、版本控制和 A/B 测试 | `Prompt`, `PromptVersion` |

**领域事件**: `AgentCreatedEvent`, `AgentPublishedEvent`, `AgentVersionCreatedEvent`

### 2.2 运行时引擎 -- Agent 执行与交互

提供 Agent 的实际执行环境，管理任务生命周期、工具调用、知识检索和会话上下文。

**子能力**:

| 子能力 | 说明 | 关键实体 |
|--------|------|---------|
| 任务执行引擎 | Agent 任务的调度、执行和状态管理，支持同步/异步模式 | `Task`, `TaskExecution` |
| 工具调用网关 | 统一管理 Agent 可调用的工具，处理鉴权、限流和结果转换 | `Tool`, `ToolInvocation` |
| 知识库集成 | 对接 Bedrock Knowledge Base，提供 RAG 检索增强能力 | `KnowledgeBase`, `KnowledgeSource` |
| 会话管理 | 维护用户与 Agent 之间的多轮对话上下文和历史记录 | `Session`, `Message` |

**领域事件**: `TaskStartedEvent`, `TaskCompletedEvent`, `ToolInvokedEvent`

### 2.3 编排协作 -- Multi-Agent 编排

支持多个 Agent 之间的工作流编排和协作通信，实现复杂业务场景的自动化处理。

**子能力**:

| 子能力 | 说明 | 关键实体 |
|--------|------|---------|
| Agent 工作流编排 | 定义多 Agent 协作的 DAG 工作流，支持条件分支和并行执行 | `Workflow`, `WorkflowStep` |
| Agent 间通信 | Agent 之间的消息传递和上下文共享机制 | `AgentMessage`, `SharedContext` |
| 编排模板 | 常见编排模式的模板化，如 Supervisor、Chain、Parallel 等 | `OrchestrationTemplate` |

**领域事件**: `WorkflowStartedEvent`, `WorkflowStepCompletedEvent`, `WorkflowCompletedEvent`

### 2.4 监控评估 -- 可观测性与质量评估

提供 Agent 运行的全方位监控和质量评估能力，覆盖执行追踪、性能分析、质量评分和成本核算。

**子能力**:

| 子能力 | 说明 | 关键实体 |
|--------|------|---------|
| 执行监控与追踪 | 基于 OpenTelemetry 的分布式追踪，记录 Agent 执行的完整链路 | `Trace`, `Span` |
| 性能指标 | 延迟、吞吐量、Token 消耗、错误率等关键指标的采集和可视化 | `Metric`, `MetricDashboard` |
| 质量评估框架 | Agent 输出质量的多维评估，包括准确性、相关性、安全性等 | `Evaluation`, `EvalCriteria` |
| 成本追踪 | 按 Agent、用户、团队维度的 Token 消耗和 API 调用成本统计 | `CostRecord`, `CostReport` |

**领域事件**: `EvaluationCompletedEvent`, `CostThresholdExceededEvent`

### 2.5 用户权限 -- 认证授权与多租户

管理平台的用户身份认证、基于角色的访问控制和资源级别的隔离。

**子能力**:

| 子能力 | 说明 | 关键实体 |
|--------|------|---------|
| 身份认证 | 基于 JWT 的用户认证，支持登录、注册和 Token 刷新 | `User`, `Token` |
| 角色授权 (RBAC) | 基于角色的访问控制，定义角色-权限映射关系 | `Role`, `Permission` |
| 资源隔离 | 按团队/项目维度的资源隔离，确保数据安全和访问边界 | `Team`, `Project` |
| 配额管理 | 按用户/团队维度的 API 调用次数、Token 消耗等配额限制 | `Quota`, `UsageRecord` |

**领域事件**: `UserCreatedEvent`, `QuotaExceededEvent`

### 2.6 平台基础 -- 基础设施与通用服务

提供跨模块共享的基础设施能力，包括 API 网关、事件总线、文件存储和配置管理。

**子能力**:

| 子能力 | 说明 | 技术实现 |
|--------|------|---------|
| API 网关 | 统一的 API 入口，处理认证、限流、路由和版本管理 | FastAPI + API Gateway |
| 事件总线 | 模块间异步通信的核心基础设施，支持发布/订阅模式 | EventBus (Outbox Pattern) |
| 文件存储 | Agent 相关的文件（知识库文档、日志、附件等）的统一存储 | S3 + 薄封装层 |
| 配置管理 | 平台运行时配置的集中管理，支持动态更新和环境隔离 | SSM Parameter Store + DynamoDB |

---

## 3. 三层技术映射

建立后端 DDD Module、前端 FSD Feature、CDK Stack 之间的对应关系，确保各层在同一能力模块上保持一致。

| 能力模块 | 后端 DDD Module | 前端 FSD Feature | CDK Stack |
|---------|----------------|-----------------|-----------|
| Agent 管理 | `modules/agents` | `features/agents` | ComputeStack, DatabaseStack |
| 运行时引擎 | `modules/runtime` | `features/runtime` | ComputeStack, ApiStack |
| 编排协作 | `modules/orchestration` | `features/orchestration` | ComputeStack |
| 监控评估 | `modules/monitoring` | `features/monitoring` | MonitoringStack |
| 用户权限 | `modules/auth` (已有) | `features/auth` | SecurityStack, DatabaseStack |
| 平台基础 | `shared` (已有) | `shared` | NetworkStack, ApiStack |

**层间交互模式**:

```
前端 (FSD)                    后端 (DDD)                   基础设施 (CDK)
┌───────────┐                ┌───────────┐                ┌─────────────┐
│ features/ │   HTTP/WS      │ modules/  │   SDK/Event    │   Stacks/   │
│ agents    │ ──────────────► │ agents    │ ──────────────► │  Compute    │
│           │   React Query   │           │   boto3/Event   │  Database   │
└───────────┘                └───────────┘                └─────────────┘
     │                            │                             │
     │ 依赖 shared/               │ 依赖 shared/                │ Props 传递
     ▼                            ▼                             ▼
┌───────────┐                ┌───────────┐                ┌─────────────┐
│ shared/   │                │ shared/   │                │  Network    │
│ api, ui   │                │ domain,   │                │  Security   │
│ hooks     │                │ infra     │                │  Monitoring │
└───────────┘                └───────────┘                └─────────────┘
```

**后端模块间通信规则** (参照已有架构规范):

- 异步通信: EventBus (Domain Events) -- 推荐
- 同步通信: `shared/domain/interfaces/` 定义跨模块接口
- 禁止: 模块间直接导入实现代码

**前端层间依赖规则** (参照 FSD 架构):

- 只能向下依赖: pages → widgets → features → entities → shared
- features 之间禁止互相依赖
- 跨 feature 通信通过 shared 层中介

---

## 4. Amazon Bedrock AgentCore 集成架构

### 4.1 AgentCore 能力边界

明确平台自建能力与 Bedrock AgentCore 托管能力之间的分工:

| 能力维度 | AgentCore 提供 | 平台自建 |
|---------|---------------|---------|
| **Agent 运行时** | Agent 执行引擎、会话管理、Memory | Agent 配置管理、版本控制、模板市场 |
| **模型调用** | Bedrock 模型 API、模型路由 | 模型选择策略、fallback 机制、成本控制 |
| **工具调用** | Action Groups、Code Interpreter | 工具注册、权限管控、调用审计 |
| **知识库** | Knowledge Base、向量检索 | 知识源管理、数据同步策略 |
| **可观测性** | CloudWatch 集成、基础 Metrics | 业务级监控、质量评估、成本分析 |
| **安全** | IAM 集成、API 级鉴权 | 用户认证、RBAC、多租户隔离 |

### 4.2 集成架构

```
┌─────────────────────────────────────────────────────┐
│                 AI Agents Platform                    │
│                                                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────────────┐ │
│  │ Agent 管理 │  │ 编排协作  │  │  监控评估         │ │
│  │ (自建)    │  │ (自建)    │  │  (自建+AgentCore) │ │
│  └─────┬─────┘  └─────┬─────┘  └────────┬──────────┘ │
│        │              │                  │             │
│  ┌─────▼──────────────▼──────────────────▼──────────┐ │
│  │           AgentCore 集成层 (Anti-Corruption)      │ │
│  │   infrastructure/external/bedrock/                 │ │
│  └─────────────────────┬────────────────────────────┘ │
└────────────────────────┼──────────────────────────────┘
                         │
         ┌───────────────▼───────────────┐
         │    Amazon Bedrock AgentCore    │
         │                               │
         │  ┌─────────┐  ┌───────────┐   │
         │  │ Agent    │  │ Knowledge │   │
         │  │ Runtime  │  │ Base      │   │
         │  └─────────┘  └───────────┘   │
         │  ┌─────────┐  ┌───────────┐   │
         │  │ Action   │  │ Memory    │   │
         │  │ Groups   │  │ Store     │   │
         │  └─────────┘  └───────────┘   │
         └───────────────────────────────┘
```

### 4.3 集成接口设计

遵循后端架构中的 Anti-Corruption Layer 模式，AgentCore 的集成通过 Infrastructure 层的适配器实现:

```
modules/runtime/
├── application/
│   └── interfaces/
│       ├── i_agent_runtime.py        # Agent 运行时抽象接口
│       ├── i_knowledge_service.py    # 知识库服务抽象接口
│       └── i_tool_gateway.py         # 工具网关抽象接口
└── infrastructure/
    └── external/
        └── bedrock/
            ├── agent_runtime_adapter.py   # AgentCore Runtime 适配器
            ├── knowledge_adapter.py       # Knowledge Base 适配器
            └── tool_gateway_adapter.py    # Action Groups 适配器
```

**关键设计原则**:

- Application 层定义抽象接口，不依赖 AgentCore SDK
- Infrastructure 层实现适配器，封装 AgentCore API 调用
- 适配器遵循 SDK-First 原则，薄封装不超过 100 行
- AgentCore SDK 异常统一转换为领域异常

---

## 5. Claude Code / Agent SDK 协作模式

### 5.1 Agent SDK 在平台中的角色

Claude Code 和 Agent SDK 在平台中扮演两个层面的角色:

**开发时 -- Claude Code 辅助开发**:

开发者使用 Claude Code 作为 AI 编程助手，遵循项目中已定义的架构规范（DDD、FSD、CDK）进行功能开发和代码审查。Claude Code 通过 `.claude/` 目录下的规范文档理解项目约束。

**运行时 -- Agent SDK 驱动执行**:

平台内部的 Agent 通过 Bedrock AgentCore 的 Agent SDK 进行任务执行。SDK 提供与模型交互、工具调用、上下文管理等核心能力。

### 5.2 开发者工作流

```
开发者
  │
  ├── Claude Code (开发环境)
  │   ├── 遵循 .claude/ 规范生成代码
  │   ├── TDD 工作流 (Red → Green → Refactor)
  │   └── 架构合规检查
  │
  └── AI Agents Platform (运行环境)
      ├── 创建/配置 Agent
      ├── 定义工具集和知识库
      ├── 编排 Multi-Agent 工作流
      └── 监控运行状态和质量
```

### 5.3 SDK 集成点

| 集成点 | SDK 能力 | 平台封装 |
|--------|---------|---------|
| Agent 创建 | `create_agent()` | Agent 配置持久化 + 版本管理 |
| Agent 调用 | `invoke_agent()` | 会话管理 + 执行追踪 |
| 工具注册 | `create_action_group()` | 工具权限管控 + 审计日志 |
| 知识库 | `create_knowledge_base()` | 数据源管理 + 同步策略 |
| Memory | `create_memory()` | 上下文持久化 + 清理策略 |

---

## 6. 数据架构

### 6.1 核心数据实体关系

```
┌──────────┐     ┌──────────────┐     ┌────────────┐
│   User   │────►│    Team      │◄────│   Project   │
└────┬─────┘     └──────────────┘     └─────┬──────┘
     │                                      │
     │ 拥有                                 │ 包含
     ▼                                      ▼
┌──────────┐     ┌──────────────┐     ┌────────────┐
│  Agent   │────►│ AgentVersion │     │  Workflow   │
└────┬─────┘     └──────────────┘     └─────┬──────┘
     │                                      │
     │ 执行                                 │ 包含
     ▼                                      ▼
┌──────────┐     ┌──────────────┐     ┌────────────┐
│  Session │────►│   Message    │     │WorkflowStep│
└────┬─────┘     └──────────────┘     └────────────┘
     │
     │ 产生
     ▼
┌──────────┐     ┌──────────────┐
│   Task   │────►│   Trace      │
└──────────┘     └──────────────┘
```

### 6.2 数据存储策略

根据数据特征选择合适的存储引擎:

| 数据类别 | 存储引擎 | 选择依据 |
|---------|---------|---------|
| 业务实体 (User, Agent, Workflow) | MySQL 8.0+ / Aurora MySQL | 关系型数据，事务一致性要求高 |
| 会话消息 (Message, ChatHistory) | DynamoDB | 高写入吞吐量，按会话分区 |
| 知识库文档 | S3 + Bedrock Knowledge Base | 非结构化数据，向量检索 |
| 监控数据 (Metrics, Traces) | CloudWatch + X-Ray | 时序数据，与 AWS 生态集成 |
| 成本记录 (CostRecord) | MySQL / DynamoDB | 聚合查询 vs 高吞吐写入 |
| 运行时配置 | SSM Parameter Store | 动态配置，环境隔离 |

### 6.3 数据流向

```
用户请求                           Agent 执行                         监控采集
   │                                 │                                 │
   ▼                                 ▼                                 ▼
┌──────┐   HTTP/WS   ┌──────────┐  SDK    ┌───────────┐  Event  ┌──────────┐
│ 前端 │ ──────────► │  后端    │ ──────► │ AgentCore │ ──────► │  监控    │
│ (FSD)│ ◄────────── │  (DDD)   │ ◄────── │           │         │  (CW)   │
└──────┘   JSON       └────┬─────┘ Result  └───────────┘         └──────────┘
                           │
                    ┌──────┼──────┐
                    ▼      ▼      ▼
               ┌──────┐┌──────┐┌──────┐
               │MySQL ││DynamoDB││ S3  │
               └──────┘└──────┘└──────┘
```

---

## 7. 扩展性设计

### 7.1 插件机制

平台通过工具插件机制支持自定义能力扩展:

**工具插件架构**:

```
modules/runtime/
├── domain/
│   └── interfaces/
│       └── i_tool_plugin.py          # 工具插件抽象接口
├── application/
│   └── services/
│       └── tool_registry_service.py  # 工具注册与发现服务
└── infrastructure/
    └── external/
        └── plugins/
            ├── builtin/              # 内置工具 (文件操作、HTTP 调用等)
            └── custom/               # 用户自定义工具
```

**插件接口定义**:

```python
class IToolPlugin(ABC):
    """工具插件抽象接口"""

    @abstractmethod
    def get_schema(self) -> ToolSchema:
        """返回工具的输入/输出 schema"""

    @abstractmethod
    async def execute(self, input: ToolInput) -> ToolOutput:
        """执行工具调用"""
```

**扩展方式**:

| 扩展类型 | 实现方式 | 示例 |
|---------|---------|------|
| 内置工具 | Python 模块，随平台部署 | 文件操作、HTTP 请求、数据库查询 |
| 自定义工具 | AgentCore Action Group | 企业内部 API 集成 |
| Lambda 工具 | Lambda 函数 + API 定义 | 独立部署的计算密集型工具 |

### 7.2 多模型支持

通过 Bedrock 的模型路由能力，平台支持多种基础模型:

```
┌─────────────────────────────────┐
│        模型选择策略层            │
│  (按任务类型、成本、性能选择)     │
├─────────────────────────────────┤
│       Amazon Bedrock             │
│  ┌─────────┐  ┌──────────────┐  │
│  │ Claude   │  │ Amazon Nova  │  │
│  │ (Sonnet, │  │              │  │
│  │  Haiku)  │  │              │  │
│  └─────────┘  └──────────────┘  │
│  ┌─────────┐  ┌──────────────┐  │
│  │ Llama   │  │   其他模型    │  │
│  └─────────┘  └──────────────┘  │
└─────────────────────────────────┘
```

**模型选择策略**:

| 策略 | 说明 | 应用场景 |
|------|------|---------|
| 成本优先 | 优先使用低成本模型 (如 Haiku) | 简单分类、格式化任务 |
| 质量优先 | 使用高能力模型 (如 Sonnet) | 复杂推理、代码生成 |
| Fallback | 主模型失败时自动切换备用模型 | 高可用要求场景 |
| A/B 测试 | 按比例分流到不同模型 | 模型评估和选型 |

### 7.3 自定义工具集成

平台为企业提供标准化的工具集成接口:

**集成流程**:

```
1. 定义工具 Schema (OpenAPI 格式)
     │
2. 实现工具逻辑 (Lambda / HTTP Endpoint)
     │
3. 在平台注册工具 (API / 管理界面)
     │
4. 配置权限和配额
     │
5. 绑定到 Agent 的 Action Group
```

**工具治理**:

| 治理维度 | 措施 |
|---------|------|
| 权限控制 | 按角色控制工具的注册、使用和管理权限 |
| 调用审计 | 记录每次工具调用的入参、出参、耗时和调用者 |
| 限流保护 | 按工具维度配置调用频率和并发数限制 |
| 版本管理 | 工具 Schema 变更的版本化管理和兼容性保证 |

---

## 附录: CDK Stack 部署依赖

```
NetworkStack
     │
     ▼
SecurityStack
     │
     ▼
DatabaseStack
     │
     ├──────────────┐
     ▼              ▼
ComputeStack    ApiStack
     │              │
     └──────┬───────┘
            ▼
     MonitoringStack
```

部署顺序严格遵循 Stack 间依赖关系，通过 CDK Props 传递实现类型安全的跨 Stack 引用。详细的 Stack 职责划分和部署规范参见 [infra/.claude/rules/architecture.md] 和 [infra/.claude/rules/deployment.md]。
