# Agent Blueprint 技术设计文档

> **版本**: 1.0
> **日期**: 2026-04-04
> **状态**: 提议 (Proposed)
> **关联 ADR**: ADR-010
> **目标里程碑**: M17 (智能协作引擎)

---

## 1. 摘要

本文档定义了 AI Agents Platform 的 **Agent Blueprint 架构** — 一种结构化的领域知识承载标准，让业务专家（非开发人员）能够将自己的业务流程（SOP）转化为可部署的 AI Agent，发布给最终用户使用。

核心设计决策：

1. **Skill 存文件系统** — 遵循 Anthropic Agent Skills 开放标准（SKILL.md），Claude Code 运行时原生加载
2. **每个上线 Agent 拥有独立 Runtime** — TESTING 阶段创建 AgentCore Runtime 容器，测试环境 = 生产环境
3. **Blueprint 是 Agent 的工作目录** — CLAUDE.md + skills/ + .claude/settings.json 构成 Claude Code 可直接 `cwd` 执行的运行环境
4. **Builder V2 是 SOP 引导式组装器** — 从"生成 JSON 配置"转变为"引导梳理业务流程 → 生成 SKILL.md + 组装工作目录"

---

## 2. 业务背景与用户画像

### 2.1 平台定位

AI Agents Platform 是基于 Amazon Bedrock AgentCore 的企业内部 AI Agents 平台。平台的核心价值不在于让开发者更快写 Agent，而在于让**不懂 AI 的业务人员**把自己的领域知识转化为可部署的 Agent。

### 2.2 核心用户画像

#### 用户 A: 业务专家（Agent 构建者）

- **代表人物**: 售后主管张姐，客服经理李总
- **特征**: 熟悉业务流程和规则，有丰富的领域经验，不懂 AI 技术
- **目标**: 将自己掌握的业务 SOP 转化为 Agent，让 Agent 替代人工处理重复性业务
- **痛点**: 看不懂 `model_id`、`temperature`、`max_tokens` 这些技术参数
- **需要的体验**: "描述业务流程 → AI 帮我组装 → 测试验证 → 上线给团队用"

#### 用户 B: 最终用户（Agent 使用者）

- **代表人物**: 一线客服人员、企业内部员工
- **特征**: 通过对话界面与 Agent 交互，不关心 Agent 如何构建
- **目标**: 快速获得业务问题的解答和流程处理
- **需要的体验**: 像和专业同事对话一样自然

#### 用户 C: 平台管理员

- **代表人物**: IT 部门运维人员
- **特征**: 管理 MCP 工具注册、审批、Runtime 监控
- **目标**: 确保 Agent 安全合规、资源可控
- **需要的体验**: 工具审批流程清晰，Agent 运行可观测

### 2.3 核心业务场景

以安克售后场景为例：

> 售后主管张姐熟悉退货、换货、投诉处理的完整流程。她希望创建一个"退货客服 Agent"，让 Agent 能查订单、检查退货条件、生成退货单、处理不了的转人工。Agent 上线后，一线客服团队通过对话界面使用这个 Agent 处理客户退货咨询。

---

## 3. 行业最佳实践研究

### 3.1 Anthropic 官方原则

来源: 《Building Effective AI Agents》白皮书 + Agent Skills 开放标准

| 原则 | 说明 | 对我们的启示 |
|------|------|------------|
| **Start simple, scale intelligently** | 从单 Agent + 少量工具开始 | Builder 应该让创建最简 Agent 极其容易 |
| **Modular design + Agent Skills** | Skills 是模块化知识封装 | 领域知识应拆分为可复用的 Skill 模块 |
| **Build observable systems** | Agent 行为需要可追溯 | 每个 Skill 步骤、工具调用都应可观测 |
| **Human-in-the-loop** | 高风险操作需人工确认 | 测试验证 + 上线审批是必须环节 |

### 3.2 Agent Skills 开放标准

Anthropic 的 Agent Skills 已发展为开放标准（agentskills.io），核心特性：

- **SKILL.md 格式**: YAML frontmatter + Markdown 正文
- **三层渐进披露**: frontmatter（始终加载, ~30 token）→ body（意图匹配时加载）→ references/（按需读取）
- **可组合**: Claude 可同时加载多个 Skills，自动协调使用
- **文件系统原生**: Claude Code 通过扫描目录发现和加载 Skills

### 3.3 MCP 与 Skills 的关系

Anthropic 官方文档明确区分：

| 层面 | MCP (Model Context Protocol) | Skills |
|------|-----|--------|
| 职责 | **What Claude CAN do** — 连接外部工具 | **HOW Claude SHOULD do it** — 流程和规则 |
| 类比 | 给员工一台电脑 | 给员工一本操作手册 |
| 存储 | 服务端运行, 通过协议连接 | 文件系统中的 SKILL.md |
| 加载 | 启动时建立连接 | 按用户意图动态加载 |

### 3.4 主流平台对比

| 能力 | OpenAI GPT Builder | Dify | Coze | 我们的目标 |
|------|---|---|---|---|
| 对话式创建 | 多轮迭代 | 表单式 | 多轮 | 多轮 + SOP 引导 |
| 工具选择 | Actions/API | 拖拽绑定 | 插件市场 | 业务能力卡片 |
| 知识库关联 | 上传文件 | RAG 集成 | 知识库 | Bedrock KB 集成 |
| 实时测试 | 预览对话 | 调试面板 | 试运行 | **专属 Runtime 真实测试** |
| 模板起步 | Explore | 模板库 | Bot Store | 模板 + Skill 库 |
| **独立运行时** | 否 | 否 | 否 | **是 (AgentCore Runtime)** |

**我们的差异化**: 面向企业内部、集成企业已有的 MCP 工具生态、每个 Agent 独立 Runtime 隔离。

### 3.5 "SOP 即 Agent" 的行业共识

多个来源反复出现同一核心观点：

> "Agents perform best when given the exact rules a human employee would use."

业务专家已有的 SOP（标准作业程序）本身就是 Agent Skill 的最佳素材。Builder 的核心价值是让这个转化过程尽可能自然。

---

## 4. 当前系统分析与差距评估

### 4.1 当前 Agent 数据模型

```python
# 当前 Agent 实体
class Agent(PydanticEntity):
    name: str
    description: str
    system_prompt: str          # ← 所有领域知识塞在这一个字符串里
    status: AgentStatus         # DRAFT → ACTIVE → ARCHIVED
    owner_id: int
    config: AgentConfig         # model_id, temperature, tool_ids, enable_memory, ...
```

### 4.2 当前 Builder (V1) 流程

```
用户输入一段话 → LLM 生成 6 个 JSON 字段 → 预览 → 确认创建 Agent
(name, description, system_prompt, model_id, temperature, max_tokens)
```

### 4.3 差距评估

| 维度 | 当前状态 | 行业最佳实践 | 差距 |
|------|---------|------------|------|
| **领域知识承载** | `system_prompt` 单字符串 | 结构化容器 (Skills + Tools + Knowledge + Memory + Guardrails) | 严重 |
| **知识复用** | 无法复用，只能复制粘贴 | Skill 模块跨 Agent 复用 | 严重 |
| **Builder 体验** | 生成技术参数 JSON | SOP 引导式业务流程梳理 | 严重 |
| **工具绑定** | tool_ids 列表，无使用条件 | 带业务语义的工具绑定 (什么时候用哪个工具) | 中等 |
| **测试验证** | 无（确认即创建） | 专属 Runtime 真实场景测试 | 严重 |
| **运行隔离** | 所有 Agent 共享 Runtime | 每个 Agent 独立 Runtime | 中等 |
| **多轮迭代** | 单轮生成，不满意重新开始 | 多轮对话式迭代 | 中等 |
| **模板集成** | templates 模块存在但 Builder 未集成 | 模板 + Skill 库作为起步选择 | 轻微 |

---

## 5. 业务流程设计

### 5.1 业务专家创建 Agent 流程 (Builder)

```
业务专家进入 Builder 页面
    │
    ├─→ 选项 A: 从 Skill 库选择已有 Skills 组装
    │   │  浏览平台 Skill 库 (按业务分类)
    │   │  选择 "退货处理"、"订单查询" 等 Skills
    │   │  → 自动组装为 Blueprint
    │   
    ├─→ 选项 B: 从模板开始
    │   │  选择 "客服 Agent 模板"
    │   │  → 模板包含预置 Skills + 工具 + 护栏
    │   │  → 在此基础上修改
    │   
    └─→ 选项 C: AI 引导创建 (核心流程)
        │
        ▼
    对话第一轮: 角色定义
        AI: "请描述这个 Agent 要处理的业务场景和角色"
        张姐: "处理客户退货咨询的售后客服"
        → AI 生成 Persona (角色 + 背景 + 语气)
        │
        ▼
    对话第二轮: 业务流程梳理
        AI: "退货流程中有哪些关键步骤？"
        张姐: "查订单、检查政策、生成退货单、处理不了转人工"
        → AI 生成 SKILL.md (退货处理流程)
        │
        ▼
    对话第三轮: 工具和知识确认
        AI: "我建议集成这些能力: [订单查询 API] [退货单 API] [转人工] [退货政策知识库]"
        张姐: "对，还需要记住客户的订单号"
        → AI 配置 ToolBindings + KnowledgeBases + MemoryConfig
        │
        ▼
    对话第四轮: 安全边界
        AI: "有哪些 Agent 绝对不能做的事？"
        张姐: "不能承诺超出政策的退款，不能泄露其他客户信息"
        → AI 生成 Guardrails
        │
        ▼
    蓝图预览 (右侧面板)
        ┌──────────────────────────────┐
        │ 👤 角色: 安克售后客服专员       │
        │ 📋 技能: 退货处理 (4步骤)      │
        │ 🔧 工具: 订单查询 + 退货单 + 转人工 │
        │ 📚 知识库: 退货政策文档         │
        │ 🧠 记忆: 开启 (订单号/诉求)    │
        │ 🛡️ 护栏: 2条安全规则          │
        └──────────────────────────────┘
        │
        ▼
    张姐可继续对话迭代: "帮我加上换货处理流程"
        → AI 生成第二个 SKILL.md
        → 蓝图预览更新
        │
        ▼
    确认 → Agent 创建 (DRAFT 状态)
```

### 5.2 Agent 测试验证流程

```
张姐点击 "开始测试"
    │
    ├── 后台: Workspace 打包上传 S3
    ├── 后台: 创建专属 AgentCore Runtime 容器
    ├── 后台: 容器启动 → 加载 CLAUDE.md + skills/
    ├── 后台: Agent 状态 → TESTING
    │
    ▼
测试沙盒界面
    │
    │  张姐输入真实业务场景:
    │  "客户说上周买的耳机坏了，想退货"
    │      │
    │      ▼
    │  Agent 回复 (路由到专属 Runtime):
    │  "很抱歉听到这个问题。请提供您的订单号，我帮您查询。"
    │  📎 引用: 退货政策文档 §3.2
    │  🔧 调用: 订单查询 API
    │      │
    │      ▼
    │  张姐评估:
    │  ✅ 正确引用了政策
    │  ✅ 调用了正确的工具
    │  ⚠️ 没有主动询问商品状况 → 需要调整 Skill
    │
    ▼
    张姐回到 Builder 修改 Skill:
    "在查询订单之前，先询问商品损坏情况并要求提供照片"
    │
    ├── 后台: 更新 SKILL.md
    ├── 后台: 重新打包上传 S3
    ├── 后台: Runtime 容器重新加载 Workspace
    │
    ▼
    再次测试 → 通过
```

### 5.3 Agent 上线发布流程

```
张姐点击 "上线发布"
    │
    ├── 系统校验: 至少完成 1 次测试对话
    ├── Agent 状态: TESTING → ACTIVE
    ├── 同一个 Runtime 容器，开放给最终用户
    │   (测试通过的即是生产运行的 — 零环境差异)
    │
    ▼
Agent 出现在最终用户的 Agent 列表中
    └── 可选: 管理员审批流程 (ACTIVE 前需 ADMIN 批准)
```

### 5.4 最终用户使用 Agent 流程

```
一线客服小王进入平台
    │
    ▼
选择 "退货客服助手" Agent
    │
    ▼
开始对话
    小王: "有个客户要退一个蓝牙耳机"
    │
    ▼
请求路由到张姐创建的专属 Runtime
    │  Runtime 中:
    │  1. CLAUDE.md → 角色: 安克售后客服专员
    │  2. skills/退货处理/SKILL.md → 触发条件匹配 "退货"
    │  3. Skill 步骤 1: 询问商品状况
    │  4. Skill 步骤 2: 调用订单查询 API (MCP 工具)
    │  5. Skill 步骤 3: 参考退货政策知识库 (Bedrock KB)
    │  6. Memory: 记住订单号和客户诉求
    │
    ▼
Agent 回复:
    "好的，请问耳机出了什么问题？能否拍张照片给我看看？"
    │
    ▼
多轮对话继续，直到退货处理完成或转人工
```

### 5.5 Skill 创建与跨 Agent 复用流程

```
场景: 张姐创建的 "退货处理" Skill 很好用，客服经理李总也想用

张姐创建 Skill (通过 Builder 或独立 Skill 编辑器)
    │
    ▼
Skill 状态: DRAFT → 张姐测试验证
    │
    ▼
Skill 状态: PUBLISHED → 进入平台 Skill 库
    │
    ▼
李总在 Builder 中创建 "全能客服 Agent"
    │  → 浏览 Skill 库，看到 "退货处理" (张姐创建)
    │  → 选择引用此 Skill
    │  → 同时选择 "换货处理"、"投诉处理" 等其他 Skill
    │
    ▼
李总的 Agent workspace:
    skills/
    ├── return-processing → 链接到 skill-library/退货处理 (张姐的)
    ├── exchange-processing → 链接到 skill-library/换货处理
    └── complaint-handling → 链接到 skill-library/投诉处理

一个 Skill 被多个 Agent 引用 (多对多关系)
```

### 5.6 Agent 运维与更新流程 (Skill 热更新)

```
场景: 公司退货政策变更，张姐需要更新退货处理 Skill

张姐编辑 "退货处理" Skill
    │  修改: "退货期限从 30 天延长到 60 天"
    │  修改: 步骤中增加 "优先推荐换货"
    │
    ▼
发布新版本 (version 1 → version 2)
    │
    ▼
平台通知: "退货处理 Skill 已更新，以下 Agent 受影响:"
    ├── 退货客服助手 (张姐的 Agent)
    └── 全能客服 Agent (李总的 Agent)
    │
    ▼
各 Agent 所有者确认更新
    │
    ├── 张姐确认 → 重新同步 Workspace → Runtime 重新加载
    └── 李总确认 → 重新同步 Workspace → Runtime 重新加载
    │
    ▼
更新完成，最终用户无感知
```

---

## 6. Agent Blueprint 架构设计

### 6.1 核心概念: Blueprint 是什么

Agent Blueprint 是 Agent 行为规范的结构化表示。它不是一个 JSON 配置文件，而是**一个 Claude Code 可以直接 `cwd` 进去运行的工作目录**。

```
agent-workspaces/{agent-id}/          ← 这就是 Blueprint 的物理形态
├── CLAUDE.md                         ← Persona + 行为规则 + 护栏
├── skills/                           ← 业务流程 (SKILL.md 文件)
│   ├── return-processing/
│   │   ├── SKILL.md                  ← 退货处理流程
│   │   └── references/               ← 参考资料 (政策详解、案例)
│   │       ├── _index.yml
│   │       └── policy-guide.md
│   └── complaint-handling/
│       ├── SKILL.md
│       └── references/
└── .claude/
    └── settings.json                 ← MCP 工具配置
```

**Blueprint 不需要"编译"为 system_prompt**。Claude Code 运行时原生支持：
- 自动读取 `CLAUDE.md` 作为 system prompt
- 自动扫描 `skills/` 目录，frontmatter 常驻内存
- 按用户意图动态加载匹配的 SKILL.md body
- 从 `.claude/settings.json` 加载 MCP 工具配置

### 6.2 领域知识六容器模型

业务专家的领域知识不能全塞进一个 `system_prompt`。Blueprint 将其拆分为六个独立容器：

| 容器 | 承载的知识 | 业务专家的理解 | 存储形式 |
|------|----------|--------------|---------|
| **Persona** (角色) | "你是谁" — 角色定义、背景、语气 | "这个 Agent 扮演什么角色" | CLAUDE.md 角色段 |
| **Skills** (技能) | "怎么做" — 业务流程步骤、行为规则 | "它会处理什么流程" | skills/ 目录下的 SKILL.md |
| **Tool Bindings** (工具) | "能用什么" — 带使用条件的工具关联 | "它能连接哪些业务系统" | .claude/settings.json + DB 记录 |
| **Knowledge Bases** (知识库) | "知道什么" — 参考文档和政策 | "它能查阅哪些文档" | DB `knowledge_base_ids` → Bedrock KB |
| **Memory Config** (记忆) | "记住什么" — 记忆策略和保留字段 | "它需要记住客户的什么信息" | DB `memory_config` + CLAUDE.md 记忆段 |
| **Guardrails** (护栏) | "不能做什么" — 安全边界和升级规则 | "它绝对不能做什么" | CLAUDE.md 安全边界段 |

**Knowledge Bases 的集成方式**: Agent 的知识库引用存储在 `agent_blueprints.knowledge_base_ids` JSON 字段中（如 `[1, 2]`）。运行时，execution 模块在构建 Agent 请求前，通过 `IKnowledgeQuerier` 执行 RAG 检索，将检索结果注入到 Agent 上下文中。知识库本身由 Bedrock Knowledge Bases 服务管理，Blueprint 只存储引用 ID。这与当前 `ActiveAgentInfo.knowledge_base_id` 的机制一致。

模型配置 (model_id, temperature 等) 不在六容器中 — 由平台自动选择或隐藏在高级设置中，业务专家不需要关心。

### 6.3 Skill — 业务 SOP 的数字化形态

**Skill 本质上就是数字化的 SOP。** 业务专家已有的标准作业程序，几乎可以直接映射为 SKILL.md。

对比：

```
人类版 SOP (张姐的工作手册):          Agent Skill 版 (SKILL.md):
─────────────────────────          ──────────────────────────
1. 确认客户身份和订单信息            ---
2. 检查退货条件:                    name: return-processing
   - 购买 30 天内？                 description: "处理退货咨询。
   - 商品在退货范围？                 当客户提到退货、退款时使用。"
   - 有损坏证据？                   ---
3. 符合条件 → 生成退货单            ## 流程步骤
4. 不符合 → 解释原因                1. 确认客户身份 [使用工具: 订单查询]
5. 客户坚持 → 转主管                2. 检查退货条件 [参考: 退货政策]
                                   3. 生成退货单 [使用工具: 退货API]
                                   4. 升级处理 [使用工具: 转人工]
                                   
                                   ## 行为规则
                                   - 先安抚情绪再处理业务
                                   - 必须引用政策来源
```

**Skill 的独立目录结构** (遵循 Anthropic Agent Skills 开放标准):

```
{skill-name}/
├── SKILL.md              ← 入口 (YAML frontmatter + 流程指令)
└── references/            ← 参考资料 (渐进披露第三层)
    ├── _index.yml         ← 资料索引
    ├── policy-guide.md    ← 退货政策详解
    └── examples.md        ← 处理案例
```

**三层渐进加载**:
1. **YAML frontmatter** (name + description) → 始终在内存，~30 token/skill
2. **SKILL.md body** → 用户意图匹配 `trigger` 时加载（流程步骤、行为规则）
3. **references/** → Skill 执行过程中按需读取（详细政策、案例模板）

### 6.4 存储分层

Skill 的真实内容在文件系统（Claude Code 消费），元信息在数据库（平台管理消费），运行时 Workspace 在 S3（AgentCore Runtime 消费）。

```
┌────────────────────────────────────────────────────────────┐
│              文件系统 — Claude Code 运行时消费                 │
│                                                            │
│  {WORKSPACE_ROOT}/                                         │
│  ├── skill-library/published/        ← 平台级 Skill 库      │
│  │   ├── return-processing/SKILL.md                        │
│  │   ├── order-inquiry/SKILL.md                            │
│  │   └── complaint-handling/SKILL.md                       │
│  │                                                         │
│  └── agent-workspaces/{agent-id}/    ← Agent 运行环境       │
│      ├── CLAUDE.md                                         │
│      ├── skills/                     ← 版本化复制 (非符号链接) │
│      │   ├── return-processing/      ← 从 skill-library v2 复制 │
│      │   └── order-inquiry/          ← 从 skill-library v1 复制 │
│      └── .claude/settings.json                             │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              S3 — AgentCore Runtime 消费                     │
│                                                            │
│  s3://agent-workspaces-{env}/                              │
│  └── {agent-id}/workspace.tar.gz    ← 打包的 Agent 工作目录 │
│                                     ← Runtime 启动时下载解压 │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              数据库 — 平台管理消费                             │
│                                                            │
│  skills 表: id, name, description, category, status,       │
│             creator_id, version, file_path, usage_count    │
│                                                            │
│  agent_blueprints 表: id, agent_id, version,               │
│                       persona_config, memory_config,       │
│                       guardrails, model_config,            │
│                       workspace_path, runtime_arn,         │
│                       workspace_s3_uri                     │
│                                                            │
│  agent_blueprint_skills 表: blueprint_id, skill_id         │
│  agent_blueprint_tool_bindings 表: blueprint_id, tool_id,  │
│                                    display_name, usage_hint│
└────────────────────────────────────────────────────────────┘
```

**为什么 Skill 必须在文件系统**: Claude Code 运行时通过扫描文件目录来发现 Skills，通过读取文件来加载 Skills。数据库中的 JSON 无法被这个机制消费。数据库只服务于平台的管理需求（搜索、权限、审计、使用计数）。

**Source of Truth 规则**: 数据库 `agent_blueprints` 表是 Blueprint 配置的权威来源。文件系统中的工作目录（CLAUDE.md + skills/ + settings.json）是从数据库 Blueprint 记录**派生生成**的产物。当 Blueprint 配置变更时，`WorkspaceManager` 负责重新生成工作目录，确保两者一致。方向始终是：数据库 → 文件系统（单向），不支持直接编辑文件系统中的文件来修改 Blueprint。

**Skill 版本化复制策略**: Agent workspace 中的 skills/ 不使用符号链接，而是**版本化复制**。当 Agent 引用 Skill v2 时，`WorkspaceManager` 将 `skill-library/published/{skill-name}/v2/` 的内容复制到 `agent-workspaces/{agent-id}/skills/{skill-name}/`。这确保了：
- Skill 更新**不会自动传播**到已有 Agent（需要 Agent 所有者确认后触发重新复制）
- 每个 Agent 的 workspace 是**自包含的**，打包为 S3 tar.gz 时不依赖外部符号链接
- 回滚简单：切回引用旧版本的 Skill 只需重新复制

**Skill 版本化存储**:
```
skill-library/
└── published/
    └── return-processing/
        ├── v1/               ← 版本 1
        │   ├── SKILL.md
        │   └── references/
        └── v2/               ← 版本 2 (最新)
            ├── SKILL.md
            └── references/
```

数据库 `skills` 表记录当前最新版本号；`agent_blueprint_skills` 关联表记录每个 Agent 引用的具体版本号：
```sql
agent_blueprint_skills (blueprint_id, skill_id, pinned_version INT NOT NULL)
```

### 6.5 Agent 状态机与独立 Runtime 生命周期

每个上线的 Agent 拥有独立的 AgentCore Runtime 容器。Runtime 在 **TESTING 阶段创建**（测试环境 = 生产环境），ACTIVE 阶段复用，ARCHIVED 阶段销毁。

```
DRAFT (编辑中)                         无 Runtime, 无容器开销
  │  Workspace 在本地文件系统构建
  │  Builder 可用本地 SDK 快速预览 (cwd 模式)
  │
  ▼  业务专家点击 "开始测试"

TESTING (测试中)                       ← 专属 Runtime 在此创建
  │  1. WorkspaceManager 打包 Workspace → 上传 S3
  │  2. AgentRuntimeManager 创建专属 AgentCore Runtime
  │  3. Runtime 容器启动 → 从 S3 下载 Workspace → 就绪
  │  4. 业务专家在测试沙盒中用真实场景验证
  │  5. 发现问题 → 修改 Skill → 重新同步 → 重启容器
  │
  ▼  验证通过, 点击 "上线发布"

ACTIVE (上线)                          同一 Runtime, 开放给最终用户
  │  无需重新创建容器 — 测试通过的即是生产运行的
  │
  ▼  Skill 更新 → Workspace 重新同步 → Runtime 滚动更新

ARCHIVED (已归档)                      Runtime 销毁, 释放资源
     Workspace S3 保留 (审计)
     本地工作目录清理
```

**核心设计原则: "What you test is what you ship"** — 消除测试与生产之间的环境差异。

### 6.6 执行路由 — 三模式

系统根据 Agent 状态自动选择执行模式：

```python
if agent_info.runtime_arn:
    # 模式 1: 专属 Runtime (TESTING / ACTIVE Agent)
    # 路由到 Agent 的独立 AgentCore Runtime 容器
    adapter = AgentCoreRuntimeAdapter(runtime_arn=agent_info.runtime_arn)

elif agent_info.workspace_path:
    # 模式 2: 本地 SDK + cwd (DRAFT Agent, Builder 快速预览)
    # 直接在 ECS Web API 进程内用 claude_agent_sdk 执行
    request.cwd = agent_info.workspace_path

else:
    # 模式 3: V1 兼容 (无 Blueprint 的旧 Agent)
    # 使用内联 system_prompt, 现有逻辑完全不变
    request.system_prompt = agent_info.system_prompt
```

**已有基础设施支撑**:
- `ClaudeAgentOptions.cwd` — SDK 已支持
- `AgentRequest.cwd` — execution 接口已定义
- `ClaudeAgentAdapter` / `AgentCoreRuntimeAdapter` — 已实现 cwd 传递

### 6.7 向后兼容

已有的 Agent（无 Blueprint, 无 Runtime）通过模式 3 继续正常工作，**无需强制迁移**。Blueprint 和独立 Runtime 作为可选增强渐进引入。

M17-C 阶段提供**可选的迁移工具**：帮助将旧 Agent 的 `system_prompt` 转换为 Blueprint 格式（CLAUDE.md + Workspace），但这不是强制性的。长期规划中，当平台完成 Blueprint 全面验证后，可逐步引导旧 Agent 迁移到 Blueprint 模式，但不会在 M17 期间废弃模式 3。

### 6.8 数据流全景

```
业务专家在 Builder 中操作
    │
    ▼
┌──────────────┐     写入       ┌──────────────────┐
│  数据库       │ ◄────────── │  BuilderService    │
│ (Source of   │              │  (创建 Blueprint   │
│  Truth)      │              │   + Skill 元信息)  │
│              │              └──────────────────┘
│ agent_       │
│ blueprints   │     触发       ┌──────────────────┐
│ skills       │ ──────────► │  WorkspaceManager  │
│ agent_       │              │                    │
│ blueprint_   │              │  1. 读取 DB Blueprint│
│ skills       │              │  2. 复制 Skill 文件  │
└──────────────┘              │  3. 生成 CLAUDE.md  │
                              │  4. 生成 settings.json│
                              └────────┬─────────┘
                                       │ 生成
                                       ▼
                              ┌──────────────────┐
                              │  本地文件系统       │
                              │  (ECS Web API 上的 │
                              │   EFS 挂载)        │
                              │                    │
                              │  agent-workspaces/ │
                              │  skill-library/    │
                              └────────┬─────────┘
                                       │ 打包上传
                                       ▼
                              ┌──────────────────┐
                              │  S3              │
                              │  workspace.tar.gz│
                              └────────┬─────────┘
                                       │ Runtime 启动时下载
                                       ▼
                              ┌──────────────────┐
                              │ AgentCore Runtime │
                              │ /workspace/       │
                              │ (容器本地文件系统)  │
                              └──────────────────┘
```

**数据流方向始终是单向**: DB → 本地文件系统 → S3 → Runtime 容器。不支持反向更新。

**EFS 的用途**: EFS 挂载在 ECS Web API 任务上（非 AgentCore Runtime），用于：
- Builder 编辑阶段：读写 Skill 草稿和 Agent Workspace
- DRAFT 阶段：本地 SDK 预览（`cwd` 指向 EFS 上的 workspace）
- 打包上传前的暂存
- AgentCore Runtime **不挂载 EFS**（AWS 服务限制），通过 S3 同步

---

## 7. Skills 模块设计

### 7.1 模块架构

新增 `skills` 模块，遵循项目的 DDD + Modular Monolith + Clean Architecture 规范：

```
backend/src/modules/skills/
├── __init__.py
├── api/
│   ├── endpoints.py              # 8 个端点 (CRUD + 发布 + 搜索)
│   ├── dependencies.py
│   └── schemas/
├── application/
│   ├── dto/skill_dto.py
│   ├── interfaces/
│   │   └── skill_file_manager.py # 文件系统操作抽象
│   └── services/skill_service.py
├── domain/
│   ├── entities/skill.py         # 元信息实体 (内容在文件系统)
│   ├── value_objects/
│   │   ├── skill_status.py       # DRAFT → PUBLISHED → ARCHIVED
│   │   └── skill_category.py     # 业务分类
│   ├── repositories/skill_repository.py
│   └── exceptions.py
└── infrastructure/
    ├── persistence/              # ORM + Repository 实现
    ├── external/
    │   └── skill_file_manager_impl.py  # 文件系统操作实现
    └── services/
        └── skill_querier_impl.py       # ISkillQuerier 跨模块接口
```

### 7.2 Skill 实体 — 只存元信息

```python
class Skill(PydanticEntity):
    """Skill 元信息实体 — SKILL.md 内容在文件系统中。"""
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    category: SkillCategory = SkillCategory.GENERAL
    trigger_description: str = Field(max_length=500, default="")
    status: SkillStatus = SkillStatus.DRAFT
    creator_id: int
    version: int = 1
    usage_count: int = 0
    file_path: str = ""  # 指向文件系统中的 Skill 目录
```

### 7.3 ISkillFileManager — 文件系统操作抽象

```python
class ISkillFileManager(ABC):
    """Skill 文件系统操作接口 (Infrastructure 层实现)。"""
    async def save_draft(self, skill_name: str, skill_md: str, references: dict[str, str] | None = None) -> str: ...
    async def publish(self, draft_path: str, skill_name: str) -> str: ...
    async def read_skill_md(self, file_path: str) -> str: ...
    async def delete_draft(self, draft_path: str) -> None: ...
    async def link_to_workspace(self, skill_path: str, workspace_path: str) -> None: ...
```

### 7.4 API 端点

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| POST | /api/v1/skills | 创建 Skill (DRAFT, 写 SKILL.md) | 当前用户 |
| GET | /api/v1/skills | 列表 (已发布 + 分类/关键词搜索) | 认证用户 |
| GET | /api/v1/skills/mine | 我的 Skills | 当前用户 |
| GET | /api/v1/skills/{id} | 详情 (含 SKILL.md 内容) | 认证用户 |
| PUT | /api/v1/skills/{id} | 更新 (仅 DRAFT, 重写 SKILL.md) | 创建者 |
| DELETE | /api/v1/skills/{id} | 删除 (仅 DRAFT, 清理文件) | 创建者 |
| POST | /api/v1/skills/{id}/publish | 发布到 Skill 库 | 创建者 |
| POST | /api/v1/skills/{id}/archive | 归档 | 创建者 |

### 7.5 跨模块接口

```python
# shared/domain/interfaces/skill_querier.py
class ISkillQuerier(ABC):
    async def get_published_skills(self, skill_ids: list[int]) -> list[SkillInfo]: ...
    async def list_published_skills(self, *, category: str | None = None, limit: int = 20) -> list[SkillSummary]: ...
```

---

## 8. Builder V2 设计

### 8.1 Builder 的新角色

Builder 从 "JSON 配置生成器" 变为 **"SOP 引导式 Agent 工作目录组装器"**：

| V1 (当前) | V2 (目标) |
|-----------|----------|
| 用户输入一段话 | AI 引导梳理业务流程 |
| LLM 生成 6 个 JSON 字段 | LLM 生成 SKILL.md + CLAUDE.md |
| 输出: JSON 配置 | 输出: Agent 工作目录 |
| 预览: 技术参数 | 预览: 业务能力卡片 |
| 确认 → DRAFT | 确认 → DRAFT → 开始测试 → 上线 |

### 8.2 前端三阶段布局

```
Phase 1: INPUT (选择起步方式)
┌─────────────────────────────────────────────┐
│ "创建你的 AI Agent"                          │
│                                             │
│ [从 Skill 库选择] [从模板开始] [AI 引导创建]  │
│                                             │
└─────────────────────────────────────────────┘

Phase 2: CONFIGURE (对话 + 预览 + 编辑)
┌──────────────────┬──────────────────────────┐
│ 💬 对话引导       │ 📋 蓝图预览               │
│                  │ 👤 角色                   │
│ [AI] 请描述...   │ 📋 技能 (Skill 卡片列表)  │
│ [你] 退货咨询    │ 🔧 工具 (能力卡片)        │
│ [AI] 有哪些步骤? │ 📚 知识库                 │
│ [你] 查订单...   │ 🧠 记忆                   │
│                  │ 🛡️ 护栏                   │
│ [迭代输入框]     │                           │
├──────────────────┴──────────────────────────┤
│ [取消] [继续调整] [开始测试 →]               │
└─────────────────────────────────────────────┘

Phase 3: TESTING (专属 Runtime 真实测试)
┌──────────────────┬──────────────────────────┐
│ 📋 蓝图摘要      │ 🧪 测试沙盒               │
│                  │                           │
│ (只读预览)       │ [模拟客户] 我的耳机坏了... │
│                  │ [Agent] 请提供订单号...    │
│                  │  📎 引用: 退货政策 §3.2   │
│                  │  🔧 调用: 订单查询 API    │
│                  │                           │
│                  │ [继续测试对话]              │
├──────────────────┴──────────────────────────┤
│ [返回修改] [上线发布 ✓]                      │
└─────────────────────────────────────────────┘
```

### 8.3 Builder AI 对话策略

Builder AI 的 system prompt 从 "生成 JSON" 变为 "SOP 引导":

```
你是企业 AI Agent 平台的构建助手。你的任务是引导业务专家将业务流程转化为 Agent 配置。

## 对话阶段
1. 角色定义: 询问 Agent 的业务场景和角色定位
2. 流程梳理: 引导用户描述业务流程的关键步骤
3. 工具匹配: 根据流程步骤推荐平台可用工具
4. 安全边界: 询问 Agent 不能做什么

## 输出格式
每轮对话后输出结构化的配置段:
- PERSONA: {...}
- SKILL: { name, trigger, steps[], rules[] }
- TOOLS: [{ tool_id, display_name, usage_hint }]
- GUARDRAILS: [{ rule, severity }]

## 平台上下文
### 可用工具
- ID:3 | 订单查询: 根据订单号查询订单状态和详情
- ID:7 | 退货单生成: 创建退货工单
- ID:12 | 转接人工: 将对话转接给人工客服
...
```

---

## 9. M17 实施方案

### 9.1 三阶段概览

| 阶段 | 周期 | 核心交付 |
|------|------|---------|
| **M17-A** 基础设施 | 2-3 周 | Skills 模块 + Blueprint 数据模型 + WorkspaceManager + AgentRuntimeManager + 执行路由 |
| **M17-B** Builder V2 | 3-4 周 | SOP 引导式 Builder + 蓝图预览 + 测试沙盒 + 上线流程 |
| **M17-C** 迁移 + 运营 | 1-2 周 | 存量 Agent 迁移 + 模板升级 + Runtime 监控 |

### 9.2 M17-A Task 清单

| # | Task | 关键交付 |
|---|------|---------|
| 1 | Skills 模块 — 领域层 | Skill 实体 + 状态机 + 仓储接口 |
| 2 | Skills 模块 — 文件系统操作 | ISkillFileManager + SKILL.md 读写 + 发布 |
| 3 | Skills 模块 — 应用服务 + API + 持久化 | 8 端点 + SkillService + ORM + ISkillQuerier |
| 4 | Agent Blueprint 数据模型 | 值对象 + DB 表 + Agent TESTING 状态 + ActiveAgentInfo 扩展 |
| 5 | WorkspaceManager | 目录生成 + 符号链接 + S3 打包上传 |
| 6 | AgentRuntimeManager | Runtime 创建/更新/销毁 (AgentCore API) |
| 7 | Agent 上线/下线 API | start-testing / go-live / take-offline 端点 + 服务编排 |
| 8 | Execution 三模式路由 + agent_entrypoint S3 同步 | 专属 Runtime / 本地 cwd / V1 兼容 |

### 9.3 M17-B Task 清单

| # | Task | 关键交付 |
|---|------|---------|
| 9 | Builder AI SOP 引导式对话策略 | builder_prompts.py + 多轮 Adapter |
| 10 | BuilderService V2 | Workspace 输出 + Runtime 触发 |
| 11 | 前端 — 蓝图预览 + Skill 卡片 | 业务能力卡片 UI |
| 12 | 前端 — 多轮对话 + 测试沙盒 + 上线流程 | 三阶段 UI + 专属 Runtime 测试 |
| 13 | CDK — S3 存储桶 + EFS | Storage Stack |

### 9.4 M17-C Task 清单

| # | Task | 关键交付 |
|---|------|---------|
| 14 | 存量迁移 + Templates 升级 | 迁移脚本 + 模板 Skill 化 |
| 15 | 全量质量检查 + 监控 | ruff + mypy + pytest + CloudWatch |

### 9.5 变更影响矩阵

| 模块 | 改动 | 说明 |
|------|------|------|
| **skills** | **新增** | 完整 DDD 模块 (Task 1-3) |
| **agents** | 中等 | Blueprint 值对象 + TESTING 状态 + 上线 API (Task 4, 7) |
| **builder** | 重构 | SOP 引导 + Workspace 输出 (Task 9-10) |
| **execution** | 最小 | 三模式路由, 约 10 行代码改动 (Task 8) |
| **agent_entrypoint** | 小 | S3 Workspace 同步 (Task 8) |
| **infra** | 中等 | S3 + EFS Stack (Task 13) |
| tool_catalog | 不变 | - |
| knowledge | 不变 | - |
| templates | 小 | M17-C 升级 |

---

## 10. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|---------|
| AgentCore Runtime 配额限制 | 中 | 高 | 监控配额; 及时销毁 ARCHIVED Agent 的 Runtime; 必要时申请提额 |
| Runtime 创建延迟 (~30-60s) | 高 | 中 | 前端展示创建进度; 异步创建 + 轮询状态; DRAFT 阶段用本地 cwd 预览 |
| Runtime 持续成本 | 高 | 中 | ARCHIVED 自动销毁; 非工作时间缩容; CloudWatch 成本告警 |
| Skill 热更新影响范围 | 低 | 高 | 异步通知 + Agent 所有者确认后才更新; 渐进式滚动 |
| S3 → Runtime 同步延迟 | 低 | 低 | workspace 包体积控制 (< 10MB); 仅启动时同步 |
| 文件系统符号链接安全 | 低 | 高 | WorkspaceManager 路径校验; 白名单目录 |
| Builder AI 生成质量 | 中 | 中 | 多轮迭代; 业务专家可手动编辑; 测试验证环节把关 |

---

## 11. 附录: 设计决策记录

| # | 决策 | 选择 | 否决的备选方案 | 理由 |
|---|------|------|-------------|------|
| 1 | Skill 存储位置 | 文件系统 (SKILL.md) | 数据库 JSON | Claude Code 运行时通过扫描文件系统加载 Skill, 数据库 JSON 无法被消费 |
| 2 | Blueprint 是否编译为 system_prompt | 不编译, 运行时原生加载 | 构建时编译为字符串 | 编译丢失渐进披露能力, 无法动态选择 Skill |
| 3 | Blueprint 是否包含运行时环境 | 不包含, 关注点分离 | 包含 Runtime 配置 | 业务知识和运行时环境是不同关注点, 不同人负责, 不同变更频率 |
| 4 | Runtime 模型 | 每 Agent 独立 Runtime | 所有 Agent 共享 Runtime | 隔离性 + 测试即生产 + 独立伸缩 |
| 5 | Runtime 创建时机 | TESTING 阶段 | ACTIVE 阶段 | 测试必须在真实运行环境中进行 |
| 6 | 元信息存储 | 数据库 (skills 表, agent_blueprints 表) | 纯文件系统 | 平台管理需求: 搜索、权限、审计、跨 Agent 引用查询 |
| 7 | Workspace 同步方式 | S3 下载 (Runtime 启动时) | EFS 挂载 | AgentCore Runtime 不支持直接挂载 EFS |
| 8 | 执行路由 | 三模式 (专属 Runtime / 本地 cwd / V1 兼容) | 统一模式 | 向后兼容 + 渐进迁移, 旧 Agent 零改动 |
| 9 | Agent 状态机 | DRAFT→TESTING→ACTIVE→ARCHIVED | DRAFT→ACTIVE→ARCHIVED | TESTING 绑定 Runtime 创建, 确保测试环境 = 生产环境 |
| 10 | Builder 输出 | 文件系统目录 (CLAUDE.md + skills/ + settings.json) | JSON 配置 | 输出即是 Claude Code 可运行的工作目录, 无需转换 |
| 11 | Skill 引用方式 | **版本化复制** (复制指定版本到 workspace) | 符号链接到 skill-library | 符号链接会导致 Skill 更新自动传播, 与确认更新机制矛盾; 复制保证 workspace 自包含, 打包 S3 无外部依赖 |
| 12 | Source of Truth | **数据库是权威来源**, 文件系统是派生产物 | 文件系统为主 | 单向数据流 (DB→文件→S3→Runtime) 简化一致性管理; 避免双向同步的复杂性 |
| 13 | 领域知识容器数量 | **六容器** (Persona + Skills + Tools + Knowledge + Memory + Guardrails) | 五容器 (无 Knowledge) | Knowledge Base 是独立的知识承载维度, 与 Skills (流程知识) 本质不同 |
