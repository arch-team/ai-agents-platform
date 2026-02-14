# 开发者入职指南 (DEVELOPER)

> 面向具有编程背景的用户，帮助你快速上手 AI Agents Platform

---

## 前提条件

- 已获取平台账户（DEVELOPER 角色）
- 了解 REST API 基本概念
- 了解 AI/LLM 基础概念

## 第一步：登录与环境熟悉

### 1.1 登录平台

访问平台 URL，使用管理员分配的账户登录。首次登录后建议修改密码。

### 1.2 了解 Dashboard

登录后进入 Dashboard 页面，可以看到：

- **Agent 概览**: 你创建的 Agent 数量和状态
- **最近对话**: 最近的对话记录
- **Token 消耗**: 本月 Token 使用量

## 第二步：创建你的第一个 Agent

### 2.1 基本创建

1. 进入 **Agent 管理** 页面
2. 点击 **创建 Agent**
3. 填写以下信息：
   - **名称**: 如 "代码审查助手"
   - **描述**: 简要描述 Agent 的用途
   - **System Prompt**: Agent 的行为指令

### 2.2 配置参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `model_id` | Haiku (默认) | 简单任务用 Haiku，复杂推理用 Sonnet/Opus |
| `temperature` | 0.7 | 越低越确定性，越高越创造性 |
| `max_tokens` | 2048 | 单次回复最大 token 数 |
| `runtime_type` | "agent" | 使用 Claude Agent SDK 执行 |

### 2.3 激活 Agent

Agent 创建后状态为 DRAFT。确认配置无误后点击 **激活**，Agent 才能用于对话。

**状态流转**: `DRAFT → ACTIVE → ARCHIVED`

## 第三步：与 Agent 对话

### 3.1 创建对话

1. 在 Agent 详情页点击 **开始对话**
2. 输入消息，Agent 将以 SSE 流式方式回复
3. 对话历史自动保存

### 3.2 使用 API 调用

```bash
# 1. 登录获取 Token
TOKEN=$(curl -s -X POST ${API_URL}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}' \
  | jq -r '.access_token')

# 2. 创建对话
CONV_ID=$(curl -s -X POST ${API_URL}/api/v1/conversations \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 1, "title": "测试对话"}' \
  | jq -r '.id')

# 3. 发送消息 (SSE 流式)
curl -N -X POST ${API_URL}/api/v1/conversations/${CONV_ID}/messages/stream \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content": "帮我写一个 Python 排序函数"}'
```

## 第四步：注册工具

### 4.1 工具类型

| 类型 | 说明 | 典型场景 |
|------|------|---------|
| MCP_SERVER | MCP 协议的服务端 | 数据库查询、文件系统访问 |
| API | REST/GraphQL API | 内部服务调用 |
| FUNCTION | 代码函数 | 简单计算、格式转换 |

### 4.2 注册 MCP Server 工具

1. 进入 **工具目录** 页面
2. 点击 **注册工具**
3. 选择 **MCP_SERVER** 类型
4. 填写 Server URL 和传输方式 (stdio/sse)
5. 提交审批

### 4.3 审批流程

```
DRAFT → 提交 → PENDING_REVIEW → ADMIN 审批 → APPROVED → 可用
                                            → REJECTED → 修改后重新提交
```

## 第五步：创建知识库

### 5.1 创建并上传文档

1. 进入 **知识库管理** 页面
2. 点击 **创建知识库**
3. 上传 PDF/TXT/MD 格式的文档
4. 等待处理完成（PROCESSING → INDEXED）

### 5.2 关联到 Agent

在 Agent 编辑页面选择关联的知识库，Agent 在对话时将自动检索相关内容作为上下文参考。

## 第六步：使用 Agent Teams

### 6.1 启用团队功能

1. 在 Agent 编辑页面，启用 `enable_teams` 选项
2. 提交团队执行任务
3. Agent 将自主组建团队、分配任务

### 6.2 查看执行进度

通过 SSE 流式端点实时查看团队执行日志和进度。

## 常见问题

### Q: 如何选择模型？

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 简单问答、信息提取 | Haiku | 速度快、成本低 |
| 代码生成、技术分析 | Sonnet | 编码能力强 |
| 复杂推理、长文档 | Opus 4.6 | 最强推理、1M 上下文 |

### Q: Agent 激活后可以修改吗？

不可以直接修改 ACTIVE 状态的 Agent 配置。需要先归档，然后创建新版本。

### Q: Token 消耗如何计费？

Token 消耗通过 **使用洞察** 页面查看。成本按 AWS Bedrock 实际使用量计算，归因到具体 Agent 和用户。
