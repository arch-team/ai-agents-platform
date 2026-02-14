# Agent 管理指南

> 本指南详细说明如何创建、配置、管理 AI Agent 以及使用 Agent Teams 功能。

---

## 目录

- [Agent 概述](#agent-概述)
- [Agent 生命周期](#agent-生命周期)
- [创建 Agent](#创建-agent)
- [配置参数说明](#配置参数说明)
- [编辑和更新 Agent](#编辑和更新-agent)
- [激活 Agent](#激活-agent)
- [归档 Agent](#归档-agent)
- [删除 Agent](#删除-agent)
- [Agent 预览测试](#agent-预览测试)
- [Agent Teams](#agent-teams)
- [API 参考](#api-参考)
- [常见问题](#常见问题)

---

## Agent 概述

Agent 是平台的核心实体，代表一个具有特定能力和行为模式的 AI 助手。每个 Agent 由以下部分组成:

- **基本信息**: 名称、描述
- **System Prompt**: 定义 Agent 行为的指令
- **模型配置**: 选择 AI 模型和调参
- **工具绑定**: Agent 可调用的外部工具（可选）
- **知识库关联**: Agent 可检索的企业知识（可选）

---

## Agent 生命周期

Agent 具有三个状态，构成不可逆的生命周期:

```
DRAFT (草稿) ──激活──> ACTIVE (已激活) ──归档──> ARCHIVED (已归档)
      │                                              ^
      └──────────────归档──────────────────────────────┘
```

| 状态 | 说明 | 可执行操作 |
|------|------|----------|
| **DRAFT** | 新创建的 Agent，不可用于对话 | 编辑、激活、归档、删除 |
| **ACTIVE** | 已激活，可用于对话和团队执行 | 编辑、归档 |
| **ARCHIVED** | 已归档（不可逆），不可用于对话 | 仅查看 |

**关键规则**:

- 只有 ACTIVE 状态的 Agent 才能发起对话
- 归档操作不可逆，如需重新使用同名 Agent，请复制创建一个新的
- 只有 DRAFT 状态的 Agent 支持物理删除

---

## 创建 Agent

### 前端操作

1. 导航到 **Agent 管理** 页面
2. 点击 **创建 Agent** 按钮
3. 填写表单:
   - **名称** (必填): 1-100 字符，同一用户下唯一
   - **描述** (可选): 最多 500 字符
   - **System Prompt** (可选，激活前必填): 最多 10000 字符
   - **模型配置** (可选): 使用默认值或自定义

### API 调用

```
POST /api/v1/agents
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "客服助手",
  "description": "处理客户常见问题",
  "system_prompt": "你是一个专业的客服助手...",
  "model_id": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**响应** (201 Created):

```json
{
  "id": 1,
  "name": "客服助手",
  "description": "处理客户常见问题",
  "system_prompt": "你是一个专业的客服助手...",
  "status": "draft",
  "owner_id": 1,
  "config": {
    "model_id": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.999,
    "runtime_type": "claude_agent",
    "enable_teams": false
  },
  "created_at": "2026-02-14T10:00:00",
  "updated_at": "2026-02-14T10:00:00"
}
```

---

## 配置参数说明

### 模型选择 (model_id)

| 模型 | model_id | 适用场景 |
|------|----------|---------|
| Claude 3.5 Haiku | `us.anthropic.claude-3-5-haiku-20241022-v1:0` | 简单对话、快速响应（默认，成本最低） |
| Claude 3.5 Sonnet | `us.anthropic.claude-3-5-sonnet-20241022-v2:0` | 代码生成、文档分析（平衡性能和成本） |
| Claude Opus 4.6 | `us.anthropic.claude-opus-4-6-v1:0` | 深度推理、复杂分析（性能最强，成本最高） |

### 生成参数

| 参数 | 取值范围 | 默认值 | 说明 |
|------|---------|--------|------|
| temperature | 0.0 - 1.0 | 1.0 | 控制输出随机性。0.0 = 确定性输出，适合精确任务；1.0 = 较高随机性，适合创意任务 |
| max_tokens | 1 - 8192 | 2048 | 单次回复最大 Token 数。越大允许越长回复，但消耗更多成本 |
| top_p | 0.0 - 1.0 | 0.999 | 核采样概率阈值。与 temperature 配合使用，一般保持默认 |

### 运行时配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| runtime_type | claude_agent | Agent 执行运行时类型 |
| enable_teams | false | 是否启用 Agent Teams 模式 |

---

## 编辑和更新 Agent

DRAFT 和 ACTIVE 状态的 Agent 均可编辑。

### 前端操作

1. 在 Agent 列表中点击目标 Agent
2. 在详情页修改需要更新的字段
3. 点击 **保存** 应用更改

### API 调用

```
PUT /api/v1/agents/{agent_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "客服助手 v2",
  "system_prompt": "你是一个升级版客服助手...",
  "temperature": 0.5
}
```

**注意**: 只需传递需要更新的字段，未传递的字段保持不变。

---

## 激活 Agent

### 激活条件

- Agent 当前状态为 DRAFT
- 名称不为空
- System Prompt 不为空

### 操作

```
POST /api/v1/agents/{agent_id}/activate
Authorization: Bearer <access_token>
```

激活成功后 Agent 状态变为 ACTIVE，可用于对话。

---

## 归档 Agent

归档操作会将 Agent 永久下线，**此操作不可逆**。

```
POST /api/v1/agents/{agent_id}/archive
Authorization: Bearer <access_token>
```

归档后:

- Agent 不可再用于新的对话
- 已有对话历史保留，仍可查看
- 如需同名 Agent，请创建新的

---

## 删除 Agent

只有 DRAFT 状态的 Agent 支持物理删除。

```
DELETE /api/v1/agents/{agent_id}
Authorization: Bearer <access_token>
```

**响应**: 204 No Content

---

## Agent 预览测试

预览功能允许快速测试 Agent 的 System Prompt 效果，不创建正式对话，不保存消息记录。

### 前端操作

在 Agent 详情页的 **测试面板** 中输入提示语，点击 **测试** 查看回复。

### API 调用

```
POST /api/v1/agents/{agent_id}/preview
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "prompt": "你好，请介绍一下你自己"
}
```

**响应**:

```json
{
  "content": "你好！我是客服助手，专门负责...",
  "model_id": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
  "tokens_input": 45,
  "tokens_output": 120
}
```

**限制**:

- Agent 必须为 ACTIVE 状态
- 单轮交互（max_turns=1）
- prompt 最大 2000 字符

---

## Agent Teams

Agent Teams 是平台的高级功能，允许将复杂任务交给 Agent 自主分解和执行，适用于需要多步推理或工具调用的场景。

### 启用 Teams

1. 在 Agent 详情页启用 **Teams 模式** 开关
2. 保存配置

或通过 API:

```
PUT /api/v1/agents/{agent_id}
Content-Type: application/json

{
  "enable_teams": true
}
```

### 提交团队执行

```
POST /api/v1/team-executions
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "agent_id": 1,
  "prompt": "请分析最近一个月的客户反馈数据，生成改进建议报告"
}
```

### 查看执行进度

团队执行是异步的，可以通过 SSE 实时查看进度:

```
GET /api/v1/team-executions/{execution_id}/stream
Authorization: Bearer <access_token>
```

也可以轮询日志:

```
GET /api/v1/team-executions/{execution_id}/logs?after_sequence=0
```

### 执行状态

| 状态 | 说明 |
|------|------|
| PENDING | 已提交，等待执行 |
| RUNNING | 正在执行 |
| COMPLETED | 执行完成 |
| FAILED | 执行失败 |
| CANCELLED | 被用户取消 |

### 取消执行

```
POST /api/v1/team-executions/{execution_id}/cancel
```

仅 PENDING 和 RUNNING 状态可取消。

---

## API 参考

### Agent 管理端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/agents` | 创建 Agent | DEVELOPER+ |
| GET | `/api/v1/agents` | Agent 列表 | DEVELOPER+ |
| GET | `/api/v1/agents/{id}` | Agent 详情 | DEVELOPER+ |
| PUT | `/api/v1/agents/{id}` | 更新 Agent | 所有者/ADMIN |
| DELETE | `/api/v1/agents/{id}` | 删除 Agent (DRAFT) | 所有者/ADMIN |
| POST | `/api/v1/agents/{id}/activate` | 激活 Agent | 所有者/ADMIN |
| POST | `/api/v1/agents/{id}/archive` | 归档 Agent | 所有者/ADMIN |
| POST | `/api/v1/agents/{id}/preview` | 预览 Agent | DEVELOPER+ |

### 对话端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/conversations` | 创建对话 |
| GET | `/api/v1/conversations` | 对话列表 |
| GET | `/api/v1/conversations/{id}` | 对话详情 (含消息历史) |
| POST | `/api/v1/conversations/{id}/messages` | 发送消息 (同步) |
| POST | `/api/v1/conversations/{id}/messages/stream` | 发送消息 (SSE 流式) |
| POST | `/api/v1/conversations/{id}/complete` | 结束对话 |

### Agent Teams 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/team-executions` | 提交团队执行 |
| GET | `/api/v1/team-executions` | 执行列表 |
| GET | `/api/v1/team-executions/{id}` | 执行详情 |
| GET | `/api/v1/team-executions/{id}/logs` | 执行日志 |
| GET | `/api/v1/team-executions/{id}/stream` | SSE 进度推送 |
| POST | `/api/v1/team-executions/{id}/cancel` | 取消执行 |

---

## 常见问题

### Q1: 我创建的 Agent 别人能看到吗？

默认情况下，每个用户只能看到自己创建的 Agent。ADMIN 角色可以查看和操作所有用户的 Agent。

### Q2: 归档 Agent 后还能恢复吗？

不能。归档是不可逆操作。如果需要类似功能的 Agent，建议创建一个新的 Agent 并复制原有配置。

### Q3: Agent Teams 和普通对话有什么区别？

| 维度 | 普通对话 | Agent Teams |
|------|---------|-------------|
| 交互方式 | 多轮即时对话 | 单次任务提交 |
| 执行模式 | 同步/流式 | 异步后台执行 |
| 适用场景 | 问答、咨询 | 复杂分析、多步任务 |
| 工具调用 | 可选 | 推荐 |
| 并发限制 | 无 | 最大 3 个并发执行 |

### Q4: temperature 设置多少合适？

- **精确任务** (数据查询、代码生成): 0.0 - 0.3
- **一般对话**: 0.5 - 0.7
- **创意任务** (写作、头脑风暴): 0.8 - 1.0

### Q5: enable_teams 开启后普通对话还能用吗？

可以。enable_teams 只是额外启用了 Agent Teams 功能，不影响普通对话。
