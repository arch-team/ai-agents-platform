# Claude Code Agent Teams 深度研究报告

> 研究日期: 2026-02-12
> 研究目标: 评估 Claude Code Agent Teams 功能用于 AI Agents 平台 Orchestration 模块的可行性
> 置信度: 高 (基于官方文档 + 社区实践 + SDK 源码验证)

---

## 目录

1. [研究背景与动机](#1-研究背景与动机)
2. [Agent Teams 核心架构](#2-agent-teams-核心架构)
3. [完整 API 和工具集](#3-完整-api-和工具集)
4. [执行模式与生命周期](#4-执行模式与生命周期)
5. [Claude Agent SDK 中的使用](#5-claude-agent-sdk-中的使用)
6. [与其他编排方案对比](#6-与其他编排方案对比)
7. [最佳实践与反模式](#7-最佳实践与反模式)
8. [用于 Orchestration 模块的可行性评估](#8-用于-orchestration-模块的可行性评估)
9. [推荐方案](#9-推荐方案)
10. [信息来源](#10-信息来源)

---

## 1. 研究背景与动机

### 1.1 项目背景

我们正在开发基于 Amazon Bedrock AgentCore + Claude Agent SDK 的企业 AI Agents 平台。在之前的调研中确认了 Claude Agent SDK 子 Agent 有**单层嵌套限制**:

> "子 Agent 不能再生成子 Agent" — 官方文档明确说明: "Subagents cannot spawn other subagents"

来源: https://code.claude.com/docs/en/sub-agents

### 1.2 核心问题

能否使用 Claude Code Agent Teams 的模式来实现 Orchestrator Agent，突破子 Agent 单层嵌套限制？

### 1.3 结论预览

**Agent Teams 没有突破子 Agent 单层嵌套限制。** Agent Teams 是一种不同的并行协作模式，它通过"Team Lead + Teammates 的对等通信"替代了"Orchestrator + 子 Agent 的层级汇报"模式，但 **Teammates 同样不能嵌套创建自己的 Team 或 Teammates**。不过，Agent Teams 的架构模式对我们设计 Orchestration 模块有重要参考价值。

---

## 2. Agent Teams 核心架构

### 2.1 功能概述

Agent Teams 于 **2026 年 2 月 5 日**随 Claude Opus 4.6 正式发布（研究预览版），是 Claude Code 的**实验性功能**，需手动启用。

它允许多个 Claude Code 实例作为一个协调团队工作：一个会话作为 Team Lead 协调工作、分配任务、综合结果；多个 Teammates 独立工作，各自拥有独立的上下文窗口，并能直接相互通信。

来源: https://code.claude.com/docs/en/agent-teams

### 2.2 架构组件

Agent Teams 由四个核心组件构成：

| 组件 | 角色 | 存储位置 |
|------|------|---------|
| **Team Lead** | 主 Claude Code 会话，创建团队、生成 Teammates、协调工作 | 主进程 |
| **Teammates** | 独立的 Claude Code 实例，执行分配的任务 | 独立进程/上下文 |
| **Task List** | 共享的任务列表，支持依赖追踪和自动解除阻塞 | `~/.claude/tasks/{team-name}/` |
| **Mailbox** | Agent 间的消息系统 | `~/.claude/teams/{team-name}/inboxes/` |

来源: https://code.claude.com/docs/en/agent-teams

### 2.3 文件系统结构

```
~/.claude/
├── teams/{team-name}/
│   ├── config.json          # 团队配置（成员列表、元数据）
│   └── inboxes/
│       ├── team-lead.json   # Lead 的收件箱
│       ├── worker-1.json    # Worker 1 的收件箱
│       └── worker-2.json    # Worker 2 的收件箱
└── tasks/{team-name}/
    ├── 1.json               # 任务 #1
    ├── 2.json               # 任务 #2
    └── 3.json               # 任务 #3
```

来源: https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea

### 2.4 团队配置文件格式

`~/.claude/teams/{team-name}/config.json`:

```json
{
  "name": "my-project",
  "description": "Working on feature X",
  "leadAgentId": "team-lead@my-project",
  "createdAt": 1706000000000,
  "members": [
    {
      "agentId": "team-lead@my-project",
      "name": "team-lead",
      "agentType": "team-lead",
      "color": "#4A90D9",
      "joinedAt": 1706000000000,
      "backendType": "in-process"
    },
    {
      "agentId": "worker-1@my-project",
      "name": "worker-1",
      "agentType": "general-purpose",
      "model": "haiku",
      "prompt": "Analyze the codebase structure...",
      "color": "#D94A4A",
      "planModeRequired": false,
      "joinedAt": 1706000001000,
      "tmuxPaneId": "in-process",
      "cwd": "/Users/me/project",
      "backendType": "in-process"
    }
  ]
}
```

来源: https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea

### 2.5 任务文件格式

`~/.claude/tasks/{team-name}/{id}.json`:

```json
{
  "id": "1",
  "subject": "Review authentication module",
  "description": "Review all files in app/services/auth/ for security vulnerabilities",
  "status": "pending",
  "owner": "",
  "activeForm": "Reviewing auth module...",
  "blockedBy": [],
  "blocks": ["3"],
  "createdAt": 1706000000000,
  "updatedAt": 1706000000000
}
```

任务状态流转: `PENDING -> IN_PROGRESS -> COMPLETED`

来源: https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/

### 2.6 通信机制

Agent Teams 使用**基于文件系统的轮询式收件箱系统**:

- **存储格式**: JSON 数组文件（非 JSONL）
- **写入路径**: 每次写入需要完整的 读取-反序列化-追加-序列化-写回 循环，O(N) 复杂度
- **并发控制**: 文件锁（file locks）防止竞态条件
- **消息投递**: 轮询检查收件箱文件
- **通信拓扑**: 以 Leader 为中心的 hub-and-spoke 模式（虽然支持 peer-to-peer，但主要模式仍然是 teammate -> leader -> teammate）

来源: https://dev.to/uenyioha/porting-claude-codes-agent-teams-to-opencode-4hol

### 2.7 与传统子 Agent 的核心区别

| 维度 | 子 Agent (Subagents) | Agent Teams |
|------|---------------------|-------------|
| **上下文** | 独立窗口，结果返回给调用方 | 独立窗口，完全独立 |
| **通信** | 仅向主 Agent 报告结果 | Teammates 之间可以直接消息通信 |
| **协调** | 主 Agent 管理所有工作 | 共享任务列表 + 自协调 |
| **嵌套** | 子 Agent 不能生成子 Agent | Teammates 不能生成 Team 或 Teammates |
| **Token 成本** | 较低（结果汇总到主上下文） | 较高（每个 Teammate 是独立 Claude 实例） |
| **Token 估算** | ~440k (3 个子 Agent) | ~800k (3 人团队) |
| **适用场景** | 聚焦任务，只需结果 | 需要讨论和协作的复杂工作 |

来源: https://code.claude.com/docs/en/agent-teams, https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/

### 2.8 关键限制: Agent Teams 是否突破了子 Agent 单层嵌套限制？

**否。** 官方文档明确声明:

> "No nested teams: teammates cannot spawn their own teams or teammates. Only the lead can manage the team."

来源: https://code.claude.com/docs/en/agent-teams (Limitations 章节)

也就是说：
- 子 Agent 不能生成子 Agent（单层限制仍然存在）
- Teammate 不能创建自己的 Team 或 Teammate（同样的单层限制）
- 只有 Team Lead 可以管理团队

Agent Teams 解决的不是"嵌套深度"问题，而是"通信模式"问题 — 从"层级汇报"变为"对等协作"。

---

## 3. 完整 API 和工具集

### 3.1 启用方式

```json
// ~/.claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

或通过环境变量:
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

来源: https://code.claude.com/docs/en/agent-teams

### 3.2 七个核心工具

Agent Teams 的完整工具集由 7 个工具调用构成:

#### 3.2.1 TeamCreate — 初始化团队

创建团队目录结构和配置文件。每个团队会话的第一个调用。

```javascript
TeamCreate({
  team_name: "feature-dev",
  description: "Building authentication feature"
})
```

**参数:**
- `team_name` (string, 必需) — 命名空间，链接任务、消息和配置
- `description` (string, 必需) — 团队用途描述

**创建的文件:**
- `~/.claude/teams/{team_name}/config.json`
- `~/.claude/tasks/{team_name}/` 目录

来源: https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/

#### 3.2.2 TaskCreate — 创建任务

每个任务成为磁盘上的一个 JSON 文件。Lead 在生成 Teammates 之前创建这些任务。

```javascript
TaskCreate({
  subject: "Design API contract",
  description: "Design the REST API contract for the user service...",
  activeForm: "Designing API contract..."
})
```

**参数:**
- `subject` (string, 必需) — 任务简短标题
- `description` (string, 必需) — 详细指令（本质上是给 Teammate 的 prompt）
- `activeForm` (string, 可选) — 任务进行中的 spinner 文本

**文件路径:** `~/.claude/tasks/{team_name}/{id}.json`

来源: https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/

#### 3.2.3 TaskUpdate — 认领和完成任务

Teammates 使用此工具来转换任务状态。

```javascript
// 认领任务
TaskUpdate({ taskId: "2", owner: "security-reviewer" })

// 开始工作
TaskUpdate({ taskId: "2", status: "in_progress" })

// 标记完成
TaskUpdate({ taskId: "2", status: "completed" })

// 添加依赖
TaskUpdate({ taskId: "3", addBlockedBy: ["1", "2"] })
```

**参数:**
- `taskId` (string, 必需) — 要更新的任务 ID
- `status` (string, 可选) — 新状态: `"in_progress"` 或 `"completed"`
- `owner` (string, 可选) — 认领任务的 Agent 名称
- `addBlockedBy` (string[], 可选) — 添加阻塞依赖

来源: https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/, https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea

#### 3.2.4 TaskList / TaskGet — 发现可用工作

```javascript
// 获取所有任务
TaskList()
// 返回: 包含 id, subject, status, owner 字段的任务对象数组

// 获取特定任务详情
TaskGet({ taskId: "2" })
```

没有集中式调度器 — 每个 Teammate 独立轮询，查找未被认领的待处理任务，并认领一个。

来源: https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/

#### 3.2.5 Task (带 team_name 参数) — 生成 Teammate

现有的 `Task` 工具增加了 `team_name` 参数，将普通子 Agent 转变为团队成员。

```javascript
Task({
  description: "Implement backend API",
  subagent_type: "general-purpose",
  name: "backend-dev",
  team_name: "feature-dev",
  model: "sonnet",
  prompt: "You are the backend developer. Implement the /api/users endpoint...",
  run_in_background: true
})
```

**参数:**
- `description` (string, 必需) — 任务描述
- `subagent_type` (string, 必需) — Agent 类型
- `name` (string, 必需) — Teammate 标识符
- `team_name` (string, 必需) — 链接到团队命名空间
- `model` (string, 可选) — 模型选择（如 "sonnet", "haiku", "opus"）
- `prompt` (string, 必需) — Teammate 的完整指令
- `run_in_background` (boolean, 可选) — 后台运行

**可用的 subagent_type 选项:**

| 类型 | 工具权限 | 默认模型 | 适用场景 |
|------|---------|---------|---------|
| `Bash` | 仅 Bash | 继承 | git 操作、命令执行 |
| `Explore` | 只读工具 | Haiku | 代码库探索、文件搜索 |
| `Plan` | 只读工具 | 继承 | 架构规划、实现策略 |
| `general-purpose` | 所有工具 | 继承 | 多步骤任务（研究+操作） |

来源: https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea, https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/

#### 3.2.6 SendMessage — Agent 间通信

这是 Agent Teams 区别于子 Agent 的核心工具。

```javascript
// 发送直接消息
SendMessage({
  type: "message",
  recipient: "frontend-dev",
  content: "API contract is ready. The /api/users endpoint returns...",
  summary: "API contract shared"
})

// 广播消息（慎用，成本随团队规模线性增长）
SendMessage({
  type: "broadcast",
  content: "All tasks completed. Please report your status.",
  summary: "Status check request"
})

// 请求关闭
SendMessage({
  type: "shutdown_request",
  recipient: "backend-dev",
  content: "All tasks complete, wrapping up"
})

// 响应关闭请求
SendMessage({
  type: "shutdown_response",
  request_id: "shutdown-123",
  approve: true
})

// 计划审批响应
SendMessage({
  type: "plan_approval_response",
  request_id: "plan-456",
  recipient: "architect",
  approve: true
})
```

**消息类型完整列表:**

| 类型 | 用途 | 方向 |
|------|------|------|
| `message` | 点对点直接消息 | 任意 Agent -> 任意 Agent |
| `broadcast` | 广播给所有 Teammates | 通常 Lead -> All |
| `shutdown_request` | 请求 Teammate 关闭 | Lead -> Teammate |
| `shutdown_response` | 确认/拒绝关闭 | Teammate -> Lead |
| `plan_approval_response` | 审批/拒绝 Teammate 的计划 | Lead -> Teammate |

**收件箱消息格式:**

```json
// 普通消息
{ "from": "backend-dev", "text": "API implementation complete", "timestamp": 1706000000, "read": false }

// 结构化消息（JSON 嵌套在 text 字段中）
{
  "from": "system",
  "text": "{\"type\": \"shutdown_request\", \"requestId\": \"shutdown-123\", \"from\": \"team-lead\", \"reason\": \"All tasks complete\", \"timestamp\": 1706000000}",
  "timestamp": 1706000000,
  "read": false
}

// 空闲通知（自动发送）
{
  "type": "idle_notification",
  "completedTaskId": "3",
  "completedStatus": "completed"
}

// 任务完成通知
{
  "type": "task_completed",
  "taskId": "2",
  "taskSubject": "Implement API endpoints"
}
```

来源: https://code.claude.com/docs/en/agent-teams, https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea

#### 3.2.7 TeamDelete — 清理

删除团队配置和所有任务文件。必须在所有 Teammates 关闭后调用。

```javascript
TeamDelete()
// 删除:
// ~/.claude/teams/{team_name}/
// ~/.claude/tasks/{team_name}/
```

来源: https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/

### 3.3 TeammateTool 内部操作（13 个操作）

除了上述公开的 7 个工具外，内部的 TeammateTool 实际包含 13 个操作:

| 操作 | 类别 | 说明 |
|------|------|------|
| `spawnTeam` | 团队生命周期 | 创建团队 |
| `discoverTeams` | 团队生命周期 | 发现可加入的团队 |
| `cleanup` | 团队生命周期 | 清理团队资源 |
| `requestJoin` | 团队生命周期 | 请求加入团队 |
| `approveJoin` | 团队生命周期 | 批准加入请求（仅 Leader） |
| `rejectJoin` | 团队生命周期 | 拒绝加入请求（仅 Leader） |
| `write` | 协调 | 给特定 Teammate 发消息 |
| `broadcast` | 协调 | 给所有 Teammates 发消息 |
| `approvePlan` | 协调 | 批准 Teammate 的计划（仅 Leader） |
| `rejectPlan` | 协调 | 拒绝 Teammate 的计划（仅 Leader） |
| `requestShutdown` | 优雅关闭 | 请求 Teammate 关闭 |
| `approveShutdown` | 优雅关闭 | 确认关闭 |
| `rejectShutdown` | 优雅关闭 | 拒绝关闭 |

来源: https://paddo.dev/blog/claude-code-hidden-swarm/

### 3.4 环境变量

生成的 Teammates 自动接收以下环境变量:

| 变量 | 说明 |
|------|------|
| `CLAUDE_CODE_TEAM_NAME` | 团队名称 |
| `CLAUDE_CODE_AGENT_ID` | Agent ID |
| `CLAUDE_CODE_AGENT_NAME` | Agent 名称 |
| `CLAUDE_CODE_AGENT_TYPE` | Agent 类型 |
| `CLAUDE_CODE_AGENT_COLOR` | Agent 标识颜色 |
| `CLAUDE_CODE_PLAN_MODE_REQUIRED` | 是否需要计划审批 |
| `CLAUDE_CODE_PARENT_SESSION_ID` | 父会话 ID |

来源: https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea, https://paddo.dev/blog/claude-code-hidden-swarm/

---

## 4. 执行模式与生命周期

### 4.1 完整生命周期

每个团队会话遵循三阶段工具调用序列:

```
=== 阶段一: 设置 (Setup) ===
1. TeamCreate()              -> 创建团队和目录
2. TaskCreate() x N          -> 定义所有任务项
3. Task(team_name) x N       -> 生成 Teammates

=== 阶段二: 执行 (Execution) — 每个 Teammate 独立执行 ===
1. TaskList()                -> 发现可用工作
2. TaskUpdate(claim)         -> 认领任务
3. [执行实际工作]
4. TaskUpdate(complete)      -> 标记完成
5. SendMessage(report)       -> 报告发现
6. 循环: 如果有更多任务 -> 回到步骤 1; 否则进入 idle 状态

=== 阶段三: 拆除 (Teardown) ===
1. shutdown_request x N      -> Lead 请求每个 Teammate 关闭
2. shutdown_response x N     -> Teammates 确认
3. TeamDelete()              -> 清理所有文件
```

来源: https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/

### 4.2 Teammate 生命周期

```
Spawn -> 加载项目上下文 -> 接收初始 Prompt -> 工作 -> Idle -> 接收新消息/任务 -> 工作 -> ... -> Shutdown
```

**关键点:**
- Teammates 加载与普通会话相同的项目上下文（CLAUDE.md, MCP servers, Skills）
- Teammates **不继承** Lead 的对话历史
- Task 文件和 SendMessage 是**唯一的协调渠道** — 没有共享内存
- Teammate 完成工作后进入 idle 状态，自动通知 Lead
- 崩溃的 Teammate 有 5 分钟心跳超时，超时后自动标记为不活跃

来源: https://code.claude.com/docs/en/agent-teams

### 4.3 任务依赖和自动解除阻塞

任务支持 `blockedBy` 和 `blocks` 依赖关系:

```javascript
// 创建有依赖的任务
TaskCreate({ subject: "Run tests", description: "..." })       // Task #1
TaskCreate({ subject: "Deploy", description: "..." })           // Task #2
TaskUpdate({ taskId: "2", addBlockedBy: ["1"] })                // Task #2 依赖 Task #1

// 当 Task #1 完成时，Task #2 自动解除阻塞
TaskUpdate({ taskId: "1", status: "completed" })
// -> Task #2 自动从 blocked 变为 pending，可被认领
```

来源: https://code.claude.com/docs/en/agent-teams

### 4.4 显示模式

| 模式 | 说明 | 要求 |
|------|------|------|
| `in-process` | 所有 Teammates 在主终端内运行，Shift+Up/Down 切换 | 任何终端 |
| `tmux` | 每个 Teammate 独立 pane，可同时查看 | tmux 或 iTerm2 |
| `auto` (默认) | 如果在 tmux 会话中使用 split panes，否则 in-process | - |

配置方式:
```json
// settings.json
{ "teammateMode": "in-process" }

// 或命令行参数
// claude --teammate-mode tmux
```

来源: https://code.claude.com/docs/en/agent-teams

### 4.5 委托模式 (Delegate Mode)

Lead 有时会自行实现任务而不是等待 Teammates。委托模式通过限制 Lead 只能使用协调工具来防止这种情况:

- **启用方式**: 创建团队后按 `Shift+Tab` 切换
- **效果**: Lead 失去 `Edit`, `Write`, `Bash` 工具的访问权限
- **保留**: 只能生成 Teammates、发送消息、管理任务列表、关闭 Teammates

来源: https://code.claude.com/docs/en/agent-teams, https://medium.com/@haberlah/configure-claude-code-to-power-your-agent-team-90c8d3bca392

### 4.6 计划审批 (Plan Approval)

用于关键或高风险任务，要求 Teammate 在实施前先制定计划:

```
Spawn an architect teammate to refactor the authentication module.
Require plan approval before they make any changes.
```

工作流:
1. Teammate 在只读的 plan mode 下工作
2. 完成规划后发送 `plan_approval_request` 给 Lead
3. Lead 审查并 approve 或 reject (附带反馈)
4. 被拒绝的 Teammate 保持 plan mode，根据反馈修改后重新提交
5. 批准后 Teammate 退出 plan mode，开始实施

来源: https://code.claude.com/docs/en/agent-teams

### 4.7 质量门控 (Hooks)

通过 Hooks 在 Teammate 完成工作或任务完成时执行规则:

- **TeammateIdle**: Teammate 即将进入 idle 状态时触发。退出码 2 可发送反馈并保持 Teammate 继续工作
- **TaskCompleted**: 任务被标记为完成时触发。退出码 2 可阻止完成并发送反馈

来源: https://code.claude.com/docs/en/agent-teams

---

## 5. Claude Agent SDK 中的使用

### 5.1 SDK 支持 Agent Teams

**是的，Claude Agent SDK (Python) 支持 Agent Teams。** 通过 `ClaudeAgentOptions` 的 `env` 参数启用:

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def run_orchestrator(prompt: str, cwd: str = "."):
    """
    使用 Agent Teams 的编排器 Agent。
    通过 env 参数启用 Agent Teams 功能。
    """
    abs_cwd = os.path.abspath(cwd)

    async for msg in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            cwd=abs_cwd,
            env={"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"},
            include_partial_messages=True,
            max_turns=200,
        ),
    ):
        # 处理消息
        await process_message(msg)
```

来源: https://medium.com/@kargarisaac/agent-teams-with-claude-code-and-claude-agent-sdk-e7de4e0cb03e

### 5.2 完整的 SDK 编排器示例

```python
"""
Orchestrator Agent (Claude Agent SDK)
使用 Agent Teams 的单阶段编排器。
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)


class MessageProcessor:
    """处理 Agent SDK 返回的消息流。"""
    def __init__(self, phase: str):
        self.phase = phase
        self.task_count = 0
        self.result_msg = None

    async def process(self, msg):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    print(f"  {block.text}")
                elif isinstance(block, ToolUseBlock):
                    tool_name = block.name
                    if tool_name == "Task":
                        self.task_count += 1
                        print(f"  [Task #{self.task_count}] {tool_name}")
                    elif tool_name in ("TeamCreate", "TaskCreate", "SendMessage", "TeamDelete"):
                        print(f"  [Team] {tool_name}")
                    else:
                        print(f"  [Tool] {tool_name}")
        elif isinstance(msg, ResultMessage):
            self.result_msg = msg


async def run_orchestrator(prompt: str, cwd: str = "."):
    abs_cwd = os.path.abspath(cwd)
    start = time.time()
    processor = MessageProcessor("run")

    async for msg in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            cwd=abs_cwd,
            env={"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"},
            include_partial_messages=True,
            max_turns=200,
        ),
    ):
        await processor.process(msg)

    duration = time.time() - start
    print(f"\nTotal: {duration:.1f}s | Tasks delegated: {processor.task_count}")


async def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Create a team to review this codebase."
    await run_orchestrator(prompt)

if __name__ == "__main__":
    asyncio.run(main())
```

来源: https://medium.com/@kargarisaac/agent-teams-with-claude-code-and-claude-agent-sdk-e7de4e0cb03e

### 5.3 ClaudeAgentOptions 完整参数

```python
@dataclass
class ClaudeAgentOptions:
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
    settings: str | None = None
    add_dirs: list[str | Path] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)        # <-- 在这里设置 Agent Teams
    extra_args: dict[str, str | None] = field(default_factory=dict)
    agents: dict[str, AgentDefinition] = field(default_factory=dict)  # 子 Agent 定义
    setting_sources: list[str] | None = None
    include_partial_messages: bool = False
    hooks: dict[str, list[HookMatcher]] | None = None
```

来源: https://platform.claude.com/docs/en/agent-sdk/python, https://github.com/anthropics/claude-agent-sdk-python

### 5.4 Agent Teams 在 AgentCore Runtime 上的部署

根据 AWS 官方示例，Claude Agent SDK 可以部署在 Amazon Bedrock AgentCore Runtime 上:

```python
#!/usr/bin/env python3
import anyio
import os
from bedrock_agentcore import BedrockAgentCoreApp
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

app = BedrockAgentCoreApp()

async def assistant_logic(prompt_text: str) -> str:
    options = ClaudeAgentOptions(
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        env={"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"},
    )
    # ... 处理逻辑
```

**重要注意事项:**
- AgentCore Runtime 使用 MicroVM 容器隔离
- Agent Teams 的文件系统操作（teams/tasks 目录）需要在容器内有写入权限
- Agent Teams 的多进程模型（tmux/iTerm2 spawn）在容器化环境中**可能受限** — 需要使用 `in-process` 模式
- **待验证**: Agent Teams 的 in-process spawn 模式是否在 AgentCore MicroVM 中正常工作

来源: https://pub.towardsai.net/deploying-claude-agent-on-amazon-bedrock-agentcore-dfcf04c29f27, https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore

### 5.5 与 MCP Server 的集成

Teammates 加载与普通 Claude Code 会话相同的 MCP 服务器配置。通过 CLAUDE.md 和项目配置，每个 Teammate 都可以访问已配置的 MCP 服务器。

```python
options = ClaudeAgentOptions(
    env={"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"},
    mcp_servers={
        "memory-server": McpServerConfig(
            command="python",
            args=["memory_mcp_server.py"],
        ),
        "tool-gateway": McpServerConfig(
            command="python",
            args=["gateway_mcp_server.py"],
        ),
    },
)
```

来源: https://code.claude.com/docs/en/agent-teams (Context and communication 章节)

---

## 6. 与其他编排方案对比

### 6.1 Agent Teams vs AgentDefinition 子 Agent

| 维度 | Agent Teams | AgentDefinition 子 Agent |
|------|------------|------------------------|
| **定义方式** | 自然语言 Prompt 描述团队结构 | `ClaudeAgentOptions.agents` 字典编程定义 |
| **通信模式** | 对等消息（peer-to-peer + hub-and-spoke） | 仅层级汇报（子 -> 父） |
| **嵌套能力** | 不支持嵌套（No nested teams） | 不支持嵌套（Subagents cannot spawn subagents） |
| **上下文隔离** | 每个 Teammate 完全独立的上下文窗口 | 每个子 Agent 独立上下文，结果汇总到父 |
| **任务管理** | 内建共享任务列表 + 依赖追踪 | 无内建任务管理，需自行实现 |
| **Token 成本** | 高（每个 Teammate 是独立 Claude 实例，~800k/3人） | 中（结果汇总到主上下文，~440k/3 个子Agent） |
| **模型选择** | 支持混合模型（Lead 用 Opus，Worker 用 Sonnet） | 支持（通过 AgentDefinition.model） |
| **适用场景** | 需要协作、讨论、相互挑战的复杂工作 | 聚焦、独立的任务 |
| **部署难度** | 需要文件系统支持，多进程模型复杂 | 较简单，进程内运行 |
| **成熟度** | 实验性（2026-02 发布） | 正式功能 |

### 6.2 Agent Teams vs A2A 协议

| 维度 | Agent Teams | A2A (Agent-to-Agent Protocol) |
|------|------------|-------------------------------|
| **协议标准** | Anthropic 私有实现 | Google 主导的开放协议标准 |
| **Agent 发现** | 本地文件系统配置 | Agent Card (JSON 元数据) 标准化发现 |
| **通信方式** | 基于文件系统的 JSON 轮询 | HTTP + SSE + JSON-RPC |
| **跨框架支持** | 仅 Claude Code / Claude Agent SDK | 跨框架、跨供应商（Google ADK, LangGraph, OpenAI SDK 等） |
| **部署范围** | 单机/单容器（共享文件系统） | 分布式/跨服务/跨网络 |
| **模型限制** | 仅 Claude 模型 | 任意模型/框架 |
| **AgentCore 支持** | 通过 Claude Agent SDK 间接支持 | AgentCore Runtime 原生支持 A2A |
| **适用场景** | Claude Code 内部的团队协作 | 异构 Agent 系统的跨服务通信 |
| **成熟度** | 实验性 | 生产就绪（AWS 已在 AgentCore 中支持） |

来源: https://aws.amazon.com/blogs/machine-learning/introducing-agent-to-agent-protocol-support-in-amazon-bedrock-agentcore-runtime/

### 6.3 Agent Teams vs Amazon Bedrock Agents Multi-Agent Collaboration

| 维度 | Agent Teams | Bedrock Multi-Agent |
|------|------------|---------------------|
| **架构模式** | Team Lead + Teammates (对等) | Supervisor + Collaborators (层级) |
| **协议** | 私有文件系统 IPC | AWS 内部 API |
| **模型支持** | 仅 Claude | Bedrock 支持的所有模型 |
| **部署方式** | 容器/本地 | 完全托管的 AWS 服务 |
| **编排控制** | 自然语言指令 | AWS 控制台/API 配置 |
| **适用场景** | Claude Code 开发工作流 | 企业级 Agent 编排 |

来源: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html

### 6.4 总结: Agent Teams 的优势和限制

**优势:**
1. **对等通信**: Teammates 可以直接消息通信，不必经过中心节点
2. **共享任务列表**: 内建的依赖管理和自动解除阻塞
3. **成本优化**: Lead 用昂贵模型协调，Workers 用便宜模型执行
4. **计划审批**: 内建的质量门控机制
5. **委托模式**: 强制 Lead 只做协调不做实现
6. **SDK 集成**: Python SDK 直接支持，可编程使用

**限制:**
1. **不支持嵌套团队**: Teammates 不能创建自己的 Team（与子 Agent 限制本质相同）
2. **单团队限制**: 一个 Lead 同时只能管理一个团队
3. **实验性功能**: 有已知问题（会话恢复、任务状态滞后、关闭缓慢）
4. **仅 Claude 生态**: 不支持其他模型或框架
5. **文件系统依赖**: 通信基于文件系统轮询，在分布式环境中受限
6. **Token 成本高**: 每个 Teammate 是独立实例，成本线性增长
7. **Leader 固定**: 无法转移领导权或提升 Teammate 为 Leader
8. **无会话恢复**: in-process Teammates 无法随会话恢复

---

## 7. 最佳实践与反模式

### 7.1 官方推荐的最佳实践

来源: https://code.claude.com/docs/en/agent-teams

#### 给 Teammates 充足的上下文

Teammates 自动加载项目上下文（CLAUDE.md, MCP, Skills），但**不继承** Lead 的对话历史。需要在 spawn prompt 中包含任务特定的详细信息:

```
Spawn a security reviewer teammate with the prompt: "Review the authentication
module at src/auth/ for security vulnerabilities. Focus on token handling,
session management, and input validation. The app uses JWT tokens stored in
httpOnly cookies. Report any issues with severity ratings."
```

#### 适当的任务粒度

- **太小**: 协调开销超过收益
- **太大**: Teammates 工作太久无检查点，增加浪费风险
- **适中**: 自包含单元，产出明确的交付物（一个函数、一个测试文件、一份审查报告）
- **建议**: 每个 Teammate 分配 5-6 个任务

#### 先计划，后并行执行

推荐的两步工作流:
1. 先在 plan mode 下制定计划（约 10k tokens）
2. 然后将计划交给团队并行执行

#### 从研究和审查开始

如果是 Agent Teams 新手，从不需要写代码的任务开始: 审查 PR、研究库、调查 bug。

#### 避免文件冲突

两个 Teammates 编辑同一文件会导致覆盖。将工作分解为每个 Teammate 拥有不同的文件集。

### 7.2 编排模式

来源: https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea

#### 模式 1: 并行专家 (Parallel Specialists)

多个专家 Agent 同时审查代码:
```
Lead -> 创建团队 -> 生成专家 (security, performance, simplicity)
专家们并行工作 -> 通过收件箱报告发现 -> Lead 综合结果
```

#### 模式 2: 流水线 (Pipeline / Sequential Dependencies)

每个阶段依赖前一个:
```
Research(Task#1) -> Planning(Task#2, blockedBy:[1])
  -> Implementation(Task#3, blockedBy:[2]) -> Testing(Task#4, blockedBy:[3])
```

#### 模式 3: 群体自组织 (Swarm / Self-Organizing)

创建无依赖的任务池，多个 Worker 竞争认领:
```
Tasks: [T1, T2, T3, T4, T5] (无依赖)
Workers: [W1, W2, W3] (相同 prompt: "持续检查未认领任务，认领-执行-完成-循环")
```

#### 模式 4: 协调式多文件重构

每个 Worker 负责不同的文件，最终任务（如更新规范）依赖所有重构任务完成。

### 7.3 反模式 (Anti-Patterns)

1. **Lead 自己实现**: Lead 应该协调，不应该自己写代码 -> 使用 Delegate Mode
2. **上下文不足**: Teammates 不继承对话历史 -> 在 spawn prompt 中提供充分上下文
3. **文件冲突**: 多个 Teammates 编辑同一文件 -> 清晰的文件所有权边界
4. **任务粒度不当**: 太大或太小都不好 -> 每个 Teammate 5-6 个适中任务
5. **无监控**: 放任团队不管 -> 定期检查进度，重定向不工作的方法
6. **滥用广播**: broadcast 成本随团队规模线性增长 -> 使用 message 定向通信
7. **用于简单任务**: 简单任务的协调开销大于收益 -> 只在真正需要并行时使用
8. **忽略清理**: 不清理团队资源 -> 始终通过 Lead 执行 TeamDelete

### 7.4 团队规模建议

- 官方文档没有明确给出最大 Teammate 数量
- 社区实践中，**3-5 个 Teammates** 是最常见且有效的配置
- Token 成本线性增长: 3 人团队 ~800k tokens，每增加一个 ~200-300k
- **建议**: 不超过 5 个 Teammates，除非有充分理由

---

## 8. 用于 Orchestration 模块的可行性评估

### 8.1 评估维度

| 评估维度 | 评分 | 说明 |
|---------|------|------|
| **嵌套限制突破** | 不可行 | Agent Teams 同样不支持嵌套 |
| **编排模式参考** | 高价值 | Task List + 依赖管理 + 消息通信模式值得借鉴 |
| **SDK 可用性** | 可用 | Python SDK 支持通过 env 参数启用 |
| **生产部署** | 风险高 | 实验性功能，已知限制多 |
| **AgentCore 兼容** | 待验证 | 需要测试 in-process 模式在 MicroVM 中的行为 |
| **多模型支持** | 有限 | 仅 Claude 系列模型 |
| **A2A 互操作** | 不支持 | 与 A2A 协议不兼容 |
| **成本效率** | 中等 | ~800k tokens/3人团队，高于子Agent方案 |

### 8.2 核心发现

1. **Agent Teams 没有解决嵌套限制问题**: 这是我们的首要研究目标，答案是明确的"否"。Teammates 不能创建自己的 Teams，与子 Agent 不能生成子 Agent 本质上是相同的限制。

2. **但 Agent Teams 的架构模式有重要参考价值**:
   - 共享任务列表 + 依赖追踪 + 自动解除阻塞
   - 基于消息的 Agent 间通信
   - 任务认领/完成的文件锁机制
   - Plan Approval 质量门控
   - Delegate Mode 强制分离协调与执行

3. **Agent Teams 本质上是 Claude Code 的开发工具特性**，不是通用的 Multi-Agent 编排框架:
   - 绑定 Claude Code 运行时
   - 依赖本地文件系统
   - 不支持分布式部署
   - 不支持跨框架/跨模型

4. **对于企业级 Multi-Agent 编排，A2A 协议 + AgentCore Runtime 是更合适的选择**:
   - AWS 原生支持
   - 跨框架互操作
   - 标准化的 Agent 发现和通信
   - 生产级别的可靠性

### 8.3 关键结论

**Agent Teams 不适合直接用于我们的 Orchestration 模块实现**，原因如下:

1. 它是 Claude Code 的实验性开发工具特性，不是生产级编排框架
2. 不支持嵌套（我们的核心需求未满足）
3. 依赖本地文件系统 IPC，不适合分布式/云部署
4. 仅支持 Claude 模型，不满足多模型需求
5. 不与 A2A 等标准协议兼容

**但 Agent Teams 的设计思路对我们有重要参考价值**，可以借鉴:
- Task List 的任务定义和依赖管理模型
- 基于消息的 Agent 间通信协议
- Plan Approval 质量门控模式
- Delegate Mode 的关注点分离
- 模型路由优化（贵模型做协调，便宜模型做执行）

---

## 9. 推荐方案

### 9.1 Orchestration 模块的推荐架构

基于本次研究结论，推荐采用以下混合方案:

```
┌─────────────────────────────────────────────────────────┐
│              Orchestrator Agent (Claude Agent SDK)        │
│  - 使用 AgentDefinition 定义子 Agent                      │
│  - 通过 Task 工具调度子 Agent                              │
│  - 参考 Agent Teams 的 Task List 模式管理任务依赖          │
│  - Plan Approval 门控机制                                  │
└──────────┬──────────────────────┬──────────────────┬─────┘
           │                      │                  │
    ┌──────▼──────┐     ┌────────▼────────┐   ┌────▼──────┐
    │ Sub-Agent 1  │     │  Sub-Agent 2     │   │ A2A Agent │
    │ (Claude SDK) │     │  (Claude SDK)    │   │ (外部框架) │
    │ Specialist   │     │  Specialist      │   │ 通过 A2A   │
    └──────────────┘     └─────────────────┘   └───────────┘
```

### 9.2 具体建议

1. **短期（当前 Sprint）**: 继续使用 Claude Agent SDK 的 `AgentDefinition` + `Task` 工具实现子 Agent 模式，这是最稳定、最成熟的方案

2. **中期（下一个 Sprint）**: 借鉴 Agent Teams 的设计思路，在 Orchestration 模块中实现:
   - 自定义的任务列表和依赖追踪系统（参考 Agent Teams 的 TaskCreate/TaskUpdate 模式）
   - Agent 间的消息通信协议（可基于数据库而非文件系统）
   - Plan Approval 质量门控
   - 模型路由策略（协调用 Opus/Sonnet，执行用 Haiku/Sonnet）

3. **长期（Phase 3+）**: 评估 A2A 协议集成:
   - AgentCore Runtime 已原生支持 A2A
   - 可实现跨框架、跨模型的 Agent 互操作
   - 解决真正的分布式 Multi-Agent 编排需求

4. **关于嵌套限制的工作方案**: 既然子 Agent 和 Agent Teams 都有单层嵌套限制，推荐以下替代方案:
   - **扁平化编排**: Orchestrator 直接管理所有子 Agent，避免嵌套需求
   - **链式调用**: 子 Agent 完成后，由 Orchestrator 根据结果调用下一个子 Agent
   - **A2A 协议**: 通过 A2A 实现真正的多层级 Agent 通信（长期方案）

---

## 10. 信息来源

### 10.1 官方文档

| 来源 | URL | 置信度 |
|------|-----|--------|
| Claude Code Agent Teams 官方文档 | https://code.claude.com/docs/en/agent-teams | 高 |
| Claude Code Subagents 官方文档 | https://code.claude.com/docs/en/sub-agents | 高 |
| Claude Agent SDK Python 参考 | https://platform.claude.com/docs/en/agent-sdk/python | 高 |
| Claude Agent SDK 概述 | https://platform.claude.com/docs/en/agent-sdk/overview | 高 |
| Claude Agent SDK 托管指南 | https://platform.claude.com/docs/en/agent-sdk/hosting | 高 |
| Claude Agent SDK GitHub | https://github.com/anthropics/claude-agent-sdk-python | 高 |

### 10.2 技术分析文章

| 来源 | URL | 置信度 |
|------|-----|--------|
| Agent Teams 架构深度分析 (alexop.dev) | https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/ | 高 |
| OpenCode 移植分析（架构对比） | https://dev.to/uenyioha/porting-claude-codes-agent-teams-to-opencode-4hol | 高 |
| Claude Code 隐藏的多 Agent 系统 | https://paddo.dev/blog/claude-code-hidden-swarm/ | 中 |
| Claude Code Swarm 编排技能指南 | https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea | 高 |
| Addy Osmani 的 Claude Code Swarms 分析 | https://addyosmani.com/blog/claude-code-agent-teams/ | 高 |

### 10.3 SDK 和 Agent Teams 实践

| 来源 | URL | 置信度 |
|------|-----|--------|
| Agent Teams with Claude Agent SDK (Python 示例) | https://medium.com/@kargarisaac/agent-teams-with-claude-code-and-claude-agent-sdk-e7de4e0cb03e | 中（Medium，403 需付费） |
| Agent Teams 实际测试经验 | https://charlesjones.dev/blog/claude-code-agent-teams-vs-subagents-parallel-development | 高 |
| Claude Code 配置 Agent Team (Medium) | https://medium.com/@haberlah/configure-claude-code-to-power-your-agent-team-90c8d3bca392 | 中 |
| Agent Teams vs Subagents 实战 | https://www.linkedin.com/pulse/claude-code-agent-teams-what-i-learned-from-testing-eric-buess-5itbc | 中 |

### 10.4 AWS/AgentCore 相关

| 来源 | URL | 置信度 |
|------|-----|--------|
| AgentCore 部署 Claude Agent | https://pub.towardsai.net/deploying-claude-agent-on-amazon-bedrock-agentcore-dfcf04c29f27 | 中 |
| AgentCore A2A 协议支持 | https://aws.amazon.com/blogs/machine-learning/introducing-agent-to-agent-protocol-support-in-amazon-bedrock-agentcore-runtime/ | 高 |
| AgentCore + Claude Agent SDK 示例 | https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore | 高 |
| Bedrock Multi-Agent Collaboration | https://docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html | 高 |

### 10.5 社区讨论

| 来源 | URL | 置信度 |
|------|-----|--------|
| Reddit: Agent Teams 设置指南 | https://www.reddit.com/r/ClaudeCode/comments/1qz8tyy/ | 中 |
| GitHub Issue: 子Agent 嵌套限制 | https://github.com/anthropics/claude-code/issues/5528 | 高 |

---

## 附录: 关键术语对照

| 英文术语 | 中文翻译 | 说明 |
|---------|---------|------|
| Agent Teams | Agent 团队 | Claude Code 的多 Agent 协作功能 |
| Team Lead | 团队 Lead | 创建和管理团队的主 Agent |
| Teammate | 团队成员 | 独立工作的 Agent 实例 |
| Subagent | 子 Agent | 传统的单层委托 Agent |
| Mailbox | 收件箱 | Agent 间消息系统 |
| Task List | 任务列表 | 共享的工作项列表 |
| Delegate Mode | 委托模式 | Lead 仅做协调的限制模式 |
| Plan Approval | 计划审批 | 实施前的质量门控 |
| Spawn | 生成 | 创建新的 Agent 实例 |
| Hub-and-spoke | 轴辐式 | 以中心节点为核心的通信拓扑 |
| Peer-to-peer | 对等式 | Agent 间直接通信 |
| A2A | Agent-to-Agent 协议 | Google 主导的开放 Agent 通信协议 |
