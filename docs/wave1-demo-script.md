# Wave 1 Demo 演示脚本

> AI Agents Platform — 种子用户 1-on-1 Demo 流程 (10 人)

---

## 1. Demo 目标

| 目标 | 说明 |
|------|------|
| 核心验证 | 让种子用户完成从注册到对话的完整闭环 |
| 收集反馈 | 发现平台可用性问题和功能缺陷 |
| 用户入职 | 每位用户至少自主创建 1 个 Agent |
| 价值展示 | 演示 AI Agent 在实际工作场景中的价值 |

**目标用户画像**: 5 名技术人员 (DEVELOPER) + 3 名产品/运营 (VIEWER->DEVELOPER) + 2 名管理者 (ADMIN)

---

## 2. 准备工作

### 2.1 环境信息

| 项目 | 值 |
|------|-----|
| **Prod API 基地址** | `http://ai-agents-prod-1419512933.us-east-1.elb.amazonaws.com` |
| **前端地址** | 同上 (前端通过同一 ALB 访问) |
| **API 文档** | `{基地址}/docs` (仅开发环境可用) |

> 以下示例中 `$BASE` 代表 Prod API 基地址。

### 2.2 Demo 前检查清单

- [ ] 确认 Prod 环境正常运行 (`GET $BASE/health`)
- [ ] 确认 3 个预置模板已 seed 并发布为 PUBLISHED 状态（见下方注意事项）
- [ ] 准备好 Demo 用的测试账号
- [ ] 准备好分角色话术（见第 6 节）
- [ ] 确认网络可访问 ALB 地址

### 2.3 预置模板状态确认

**重要**: 种子脚本 `backend/scripts/seed_templates.py` 仅定义了模板数据，**没有自动执行和发布逻辑**。模板创建后默认为 DRAFT 状态，需要手动发布。

**手动发布步骤**:

1. 使用管理员账号登录获取 Token
2. 通过 API 创建模板（POST 请求）
3. 调用发布接口将模板从 DRAFT 转为 PUBLISHED

```bash
# 步骤 1: 管理员登录
TOKEN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "AdminPass123"}' \
  | jq -r '.access_token')

# 步骤 2: 创建"代码审查助手"模板
TEMPLATE_ID=$(curl -s -X POST "$BASE/api/v1/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "代码审查助手",
    "description": "审查代码质量、安全性和最佳实践，提供改进建议",
    "category": "code_assistant",
    "tags": ["代码审查", "安全", "最佳实践"],
    "system_prompt": "你是一位资深的代码审查专家。请按以下维度审查代码:\n1. **正确性**: 逻辑是否正确，边界条件是否处理\n2. **安全性**: 是否存在 SQL 注入、XSS、敏感信息泄露等问题\n3. **性能**: 算法复杂度、数据库查询优化、内存使用\n4. **可读性**: 命名规范、注释质量、代码结构\n5. **可维护性**: SOLID 原则、DRY 原则、适当抽象\n6. **测试**: 测试覆盖率、测试质量\n\n对每个问题给出严重等级 (Critical/Major/Minor) 和具体修改建议。",
    "model_id": "anthropic.claude-sonnet-4-20250514",
    "temperature": 0.2,
    "max_tokens": 4096
  }' | jq -r '.id')

# 步骤 3: 发布模板
curl -s -X POST "$BASE/api/v1/templates/$TEMPLATE_ID/publish" \
  -H "Authorization: Bearer $TOKEN"
```

对"会议纪要助手"和"技术文档写手"重复步骤 2-3（参数见附录 A）。

---

## 3. 完整演示流程

### 流程概览

```
注册账号 → 登录 → 浏览模板市场 → 从模板创建 Agent → 激活 Agent → 发起对话 → 查看 Insights
```

---

### 步骤 1: 注册账号

**操作说明**: 为演示用户创建账号。

**前端操作**:
1. 打开浏览器访问平台地址
2. 点击登录页面下方的"注册"链接，跳转到 `/register`
3. 填写邮箱、姓名和密码（密码要求: 8-128 位，含大小写字母和数字）
4. 点击"注册"按钮

**curl 命令**:

```bash
curl -X POST "$BASE/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "name": "张三"
  }'
```

**预期结果**:

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "张三",
  "role": "viewer",
  "is_active": true
}
```

> **注意**: 新注册用户默认为 `viewer` 角色。如需 DEVELOPER 或 ADMIN 权限，需管理员通过 Admin API 调整。注册接口限流为每小时 3 次。

---

### 步骤 2: 登录

**操作说明**: 使用注册的邮箱和密码登录平台。

**前端操作**:
1. 在登录页面 (`/login`) 输入邮箱和密码
2. 点击"登录"按钮
3. 登录成功后自动跳转到控制台首页 (`/`)

**curl 命令**:

```bash
curl -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

**预期结果**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

> **后续请求**: 将 `access_token` 放入 HTTP Header `Authorization: Bearer <token>`。Access Token 有效期 30 分钟，过期后用 Refresh Token 续期。登录接口限流为每分钟 5 次。

```bash
# 保存 Token 供后续使用
export TOKEN="<access_token 值>"
```

---

### 步骤 3: 查看控制台首页

**操作说明**: 登录后首先看到 Dashboard 概览。

**前端操作**:
1. 登录后自动进入首页 (`/`)
2. 查看统计卡片: Agent 总数、对话总数、团队执行总数

**curl 命令**:

```bash
# 获取当前用户信息
curl -X GET "$BASE/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# 获取 Dashboard 统计
curl -X GET "$BASE/api/v1/stats/summary" \
  -H "Authorization: Bearer $TOKEN"
```

**预期结果** (新用户):

```json
{
  "agents_total": 0,
  "conversations_total": 0,
  "team_executions_total": 0
}
```

---

### 步骤 4: 浏览模板市场

**操作说明**: 查看预置的 Agent 模板，了解平台提供的开箱即用能力。

**前端操作**:
1. 点击左侧导航栏的"模板"菜单，进入模板列表页 (`/templates`)
2. 浏览已发布的模板卡片（代码审查助手、会议纪要助手、技术文档写手）
3. 点击任意模板查看详情 (`/templates/:templateId`)

**curl 命令**:

```bash
# 获取已发布模板列表
curl -X GET "$BASE/api/v1/templates?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# 查看模板详情（假设 ID=1）
curl -X GET "$BASE/api/v1/templates/1" \
  -H "Authorization: Bearer $TOKEN"
```

**预期结果**:

```json
{
  "items": [
    {
      "id": 1,
      "name": "代码审查助手",
      "description": "审查代码质量、安全性和最佳实践，提供改进建议",
      "category": "code_assistant",
      "status": "published",
      "tags": ["代码审查", "安全", "最佳实践"],
      "is_featured": true,
      "usage_count": 0
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

**Demo 话术**: "这里是模板市场，我们预置了几个常用的 Agent 模板，你可以基于模板快速创建自己的 Agent，无需从零编写 System Prompt。"

---

### 步骤 5: 从模板创建 Agent

**操作说明**: 参考模板的 System Prompt 和参数配置，创建一个自己的 Agent。

**前端操作**:
1. 在模板详情页查看 System Prompt 和配置参数
2. 点击左侧导航栏的"Agent 管理"(`/agents`)
3. 点击右上角"创建 Agent"按钮，进入创建页面 (`/agents/create`)
4. 填写 Agent 名称、描述、System Prompt（可复制模板中的 Prompt）
5. 设置模型参数 (model_id, temperature, max_tokens)
6. 点击"创建"按钮

**curl 命令**:

```bash
# 创建 Agent（使用代码审查助手的 System Prompt）
curl -X POST "$BASE/api/v1/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的代码审查助手",
    "description": "帮我审查 Python 代码质量",
    "system_prompt": "你是一位资深的代码审查专家。请按以下维度审查代码:\n1. 正确性: 逻辑是否正确\n2. 安全性: 是否存在安全问题\n3. 性能: 算法复杂度和优化\n4. 可读性: 命名和结构\n5. 可维护性: 设计原则\n\n对每个问题给出严重等级和修改建议。",
    "model_id": "anthropic.claude-sonnet-4-20250514",
    "temperature": 0.2,
    "max_tokens": 4096
  }'
```

**预期结果**:

```json
{
  "id": 1,
  "name": "我的代码审查助手",
  "description": "帮我审查 Python 代码质量",
  "status": "draft",
  "owner_id": 1,
  "config": {
    "model_id": "anthropic.claude-sonnet-4-20250514",
    "temperature": 0.2,
    "max_tokens": 4096,
    "top_p": 0.999,
    "runtime_type": "agent",
    "enable_teams": false
  },
  "created_at": "2026-02-18T...",
  "updated_at": "2026-02-18T..."
}
```

> **说明**: Agent 创建后为 DRAFT 状态，需要激活才能用于对话。

---

### 步骤 6: 激活 Agent

**操作说明**: 将 Agent 从 DRAFT 激活为 ACTIVE 状态。

**前端操作**:
1. 在 Agent 列表 (`/agents`) 点击刚创建的 Agent 进入详情页 (`/agents/:agentId`)
2. 点击"激活"按钮
3. Agent 状态变为 ACTIVE

**curl 命令**:

```bash
# 激活 Agent（假设 ID=1）
curl -X POST "$BASE/api/v1/agents/1/activate" \
  -H "Authorization: Bearer $TOKEN"
```

**预期结果**:

```json
{
  "id": 1,
  "name": "我的代码审查助手",
  "status": "active"
}
```

> **状态流转**: DRAFT -> ACTIVE -> ARCHIVED（归档不可逆）

---

### 步骤 7: (可选) Agent 预览测试

**操作说明**: 在正式对话前，快速测试 Agent 的回复效果。预览为单轮测试，不创建对话记录。

**前端操作**:
1. 在 Agent 详情页的测试面板中输入测试消息
2. 查看 Agent 回复

**curl 命令**:

```bash
# 预览测试（单轮，不持久化）
curl -X POST "$BASE/api/v1/agents/1/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "请帮我审查这段代码:\ndef add(a, b):\n    return a + b"
  }'
```

**预期结果**:

```json
{
  "content": "这段代码整体简单，但我有以下审查意见:\n\n**Minor - 类型提示缺失**\n建议添加类型提示...",
  "model_id": "anthropic.claude-sonnet-4-20250514",
  "tokens_input": 45,
  "tokens_output": 120
}
```

---

### 步骤 8: 发起对话

**操作说明**: 创建正式对话并与 Agent 交互。

**前端操作**:
1. 点击左侧导航栏的"对话" (`/chat`)
2. 创建新对话，选择已激活的 Agent
3. 在消息输入框输入问题，按回车或点击发送
4. 观看 Agent 以流式方式逐字回复

**curl 命令**:

```bash
# 步骤 1: 创建对话
CONV_ID=$(curl -s -X POST "$BASE/api/v1/conversations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 1,
    "title": "代码审查会话"
  }' | jq -r '.id')

echo "对话 ID: $CONV_ID"

# 步骤 2: 发送消息（同步模式）
curl -X POST "$BASE/api/v1/conversations/$CONV_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请帮我审查以下 Python 代码:\n\ndef get_user(id):\n    conn = sqlite3.connect(\"db.sqlite\")\n    cursor = conn.execute(f\"SELECT * FROM users WHERE id = {id}\")\n    return cursor.fetchone()"
  }'

# 步骤 2 (替代): 发送消息（流式模式，SSE）
curl -N -X POST "$BASE/api/v1/conversations/$CONV_ID/messages/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请帮我审查以下 Python 代码:\n\ndef get_user(id):\n    conn = sqlite3.connect(\"db.sqlite\")\n    cursor = conn.execute(f\"SELECT * FROM users WHERE id = {id}\")\n    return cursor.fetchone()"
  }'
```

**预期结果** (同步模式):

```json
{
  "id": 1,
  "conversation_id": 1,
  "role": "assistant",
  "content": "## 代码审查报告\n\n### Critical - SQL 注入漏洞\n...",
  "token_count": 256,
  "created_at": "2026-02-18T..."
}
```

**预期结果** (流式模式，SSE 事件):

```
data: {"content": "## 代码", "done": false}
data: {"content": "审查报告", "done": false}
data: {"content": "\n\n### Critical", "done": false}
...
data: {"content": "", "done": true, "message_id": 1, "token_count": 256}
```

**Demo 话术**: "看，Agent 已经发现了 SQL 注入漏洞，并给出了具体的修改建议。你可以把日常工作中的代码片段发给它审查。"

---

### 步骤 9: 查看对话历史

**操作说明**: 查看之前的对话记录。

**前端操作**:
1. 在对话页面 (`/chat`) 左侧对话列表中选择历史对话
2. 查看完整的消息历史

**curl 命令**:

```bash
# 获取对话列表
curl -X GET "$BASE/api/v1/conversations?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# 获取对话详情（含消息历史）
curl -X GET "$BASE/api/v1/conversations/$CONV_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 步骤 10: 结束对话

**操作说明**: 结束当前对话。

**前端操作**:
1. 点击对话区域右上角的"结束"按钮

**curl 命令**:

```bash
curl -X POST "$BASE/api/v1/conversations/$CONV_ID/complete" \
  -H "Authorization: Bearer $TOKEN"
```

**预期结果**: 对话状态变为 `completed`，不再接受新消息。

---

### 步骤 11: 查看使用洞察 (Insights)

**操作说明**: 查看 Token 消耗和使用统计数据。

**前端操作**:
1. 点击左侧导航栏的"使用洞察" (`/insights`)
2. 查看概览统计（Agent 数量、调用次数、Token 消耗、成本）
3. 查看按 Agent 维度的成本归因
4. 查看使用趋势图

**curl 命令**:

```bash
# 获取 Insights 概览
curl -X GET "$BASE/api/v1/insights/summary" \
  -H "Authorization: Bearer $TOKEN"

# 获取按 Agent 的成本归因
curl -X GET "$BASE/api/v1/insights/cost-breakdown" \
  -H "Authorization: Bearer $TOKEN"

# 获取使用趋势
curl -X GET "$BASE/api/v1/insights/usage-trends" \
  -H "Authorization: Bearer $TOKEN"
```

**预期结果**:

```json
{
  "total_agents": 1,
  "active_agents": 1,
  "total_invocations": 2,
  "total_cost": 0.0015,
  "total_tokens": 512,
  "period": {
    "start_date": "2026-01-19",
    "end_date": "2026-02-18"
  }
}
```

**Demo 话术**: "这是使用洞察页面，你可以看到每个 Agent 消耗了多少 Token、产生了多少成本。管理者可以看到全部数据，普通用户只看到自己的。"

---

## 4. 前端页面路径汇总

| 页面 | 路径 | 说明 |
|------|------|------|
| 登录 | `/login` | 公开页面 |
| 注册 | `/register` | 公开页面 |
| 控制台首页 | `/` | Dashboard 统计概览 |
| Agent 列表 | `/agents` | 我的 Agent 管理 |
| 创建 Agent | `/agents/create` | 新建 Agent 表单 |
| Agent 详情 | `/agents/:agentId` | Agent 配置和预览 |
| 对话 | `/chat` | 对话列表和消息 |
| 对话详情 | `/chat/:conversationId` | 指定对话 |
| 团队执行 | `/team-executions` | Agent Teams 执行记录 |
| 模板列表 | `/templates` | 模板市场浏览 |
| 模板详情 | `/templates/:templateId` | 模板配置查看 |
| 工具列表 | `/tools` | 工具目录 |
| 工具详情 | `/tools/:toolId` | 工具配置 |
| 知识库 | `/knowledge` | 知识库管理 |
| 知识库详情 | `/knowledge/:knowledgeBaseId` | 知识库文档管理 |
| 使用洞察 | `/insights` | Token 消耗和成本分析 |
| 评测 | `/evaluation` | Agent 质量评测 |
| 评测详情 | `/evaluation/:suiteId` | 测试套件管理 |
| 评测运行 | `/evaluation/runs` | 评测执行记录 |

---

## 5. FAQ 和常见问题

### Q1: 注册时提示"注册功能已关闭"？

平台可通过 `REGISTRATION_ENABLED` 环境变量控制注册开关。如遇此问题，联系管理员开启注册，或由管理员通过 Admin API 直接创建账号。

### Q2: 登录后页面显示空白或报错？

- 检查浏览器控制台是否有网络错误
- 确认 API 地址可正常访问: `curl $BASE/health`
- 确认使用的是 Chrome 90+ 等现代浏览器

### Q3: 创建 Agent 提示"名称已存在"？

同一用户下 Agent 名称不可重复。请使用不同名称，或删除已有的同名草稿 Agent。

### Q4: 激活 Agent 失败？

激活需满足以下条件:
- Agent 名称不能为空
- System Prompt 不能为空
- Agent 当前状态必须为 DRAFT

### Q5: 对话没有回复或回复很慢？

可能原因:
1. **模型负载**: 高峰期模型响应可能较慢，稍等片刻
2. **网络问题**: 检查与平台的网络连接
3. **Token 超限**: 对话历史过长时，尝试结束当前对话开始新对话
4. **Agent 未激活**: 确认 Agent 状态为 ACTIVE

### Q6: 如何删除 Agent？

仅 DRAFT 状态的 Agent 可删除。已激活 (ACTIVE) 的 Agent 只能归档 (ARCHIVED)，归档后不可恢复。

### Q7: Token 是什么？费用如何计算？

Token 是 AI 模型处理文本的基本单位，约 3-4 个中文字符对应 1 个 Token。每次对话会消耗 input Token（你的提问）和 output Token（Agent 的回复）。在使用洞察页面可查看详细消耗。

### Q8: 模板列表为空？

预置模板需要管理员手动创建并发布。请联系管理员确认已执行种子数据导入。

### Q9: Access Token 过期后怎么办？

前端会自动使用 Refresh Token 续期。如果 Refresh Token 也过期，需要重新登录。通过 API 使用时:

```bash
curl -X POST "$BASE/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<你的 refresh_token>"}'
```

### Q10: 如何修改已激活的 Agent 配置？

激活后仍可编辑 Agent 的名称、描述、System Prompt 和模型参数。在 Agent 详情页直接修改并保存。

---

## 6. 话术建议

### 6.1 面向技术人员 (DEVELOPER)

**开场白**: "这是我们基于 Amazon Bedrock 构建的内部 AI Agent 平台。和直接用 ChatGPT 不同，你可以创建定制化的 Agent，配置专属的 System Prompt，让 Agent 专注于特定任务场景。"

**核心卖点**:
- "你可以把代码审查、文档编写等重复性工作交给 Agent"
- "System Prompt 可以精细定制，比通用 AI 更准确"
- "所有对话数据和 Token 消耗都可追踪，成本透明"
- "未来会支持 Agent Teams（多 Agent 协作）和自定义工具调用"
- "API 完备，可以集成到你的工作流中"

**演示重点**: 展示创建 Agent -> 配置 System Prompt -> 对话的完整流程，强调 API 的灵活性。

### 6.2 面向产品/运营

**开场白**: "这是一个 AI 助手平台，你不需要写代码就能创建自己的 AI 助手。我们已经准备了一些模板，你可以直接使用或者在此基础上调整。"

**核心卖点**:
- "有现成的模板，一键就能创建会议纪要助手、文档写作助手"
- "不需要技术背景，在网页上操作就行"
- "你创建的 Agent 只有你自己能用，数据安全"
- "可以看到使用了多少 AI 资源，帮助评估价值"

**演示重点**: 从模板创建 Agent 的简便流程，强调"零代码"和"模板"。

### 6.3 面向管理者 (ADMIN)

**开场白**: "这是我们自建的 AI Agent 平台，核心目标是让每个团队都能快速接入 AI 能力，同时保证安全可控和成本透明。"

**核心卖点**:
- "集中管理所有 AI Agent，统一安全策略和权限控制"
- "使用洞察页面可以看到全公司的 Token 消耗和成本分析"
- "审计日志记录所有操作，满足合规要求"
- "RBAC 权限控制: Admin 管理全局，Developer 创建 Agent，Viewer 浏览"
- "相比直接采购 SaaS AI 产品，自建平台更灵活、数据更安全"

**演示重点**: Dashboard 概览 -> Insights 成本分析 -> 审计日志，强调"管控"和"可视化"。

---

## 附录 A: 预置模板完整参数

### 代码审查助手

```json
{
  "name": "代码审查助手",
  "description": "审查代码质量、安全性和最佳实践，提供改进建议",
  "category": "code_assistant",
  "tags": ["代码审查", "安全", "最佳实践"],
  "system_prompt": "你是一位资深的代码审查专家。请按以下维度审查代码:\n1. **正确性**: 逻辑是否正确，边界条件是否处理\n2. **安全性**: 是否存在 SQL 注入、XSS、敏感信息泄露等问题\n3. **性能**: 算法复杂度、数据库查询优化、内存使用\n4. **可读性**: 命名规范、注释质量、代码结构\n5. **可维护性**: SOLID 原则、DRY 原则、适当抽象\n6. **测试**: 测试覆盖率、测试质量\n\n对每个问题给出严重等级 (Critical/Major/Minor) 和具体修改建议。",
  "model_id": "anthropic.claude-sonnet-4-20250514",
  "temperature": 0.2,
  "max_tokens": 4096
}
```

### 会议纪要助手

```json
{
  "name": "会议纪要助手",
  "description": "整理会议记录、提取关键决策和行动项",
  "category": "workflow_automation",
  "tags": ["会议", "纪要", "行动项"],
  "system_prompt": "你是一位会议纪要整理专家。请按以下格式整理会议内容:\n\n## 会议基本信息\n- 日期/时间/参会人\n\n## 议题摘要\n- 每个议题的讨论要点 (简洁)\n\n## 关键决策\n- 列出所有达成共识的决策\n\n## 行动项 (Action Items)\n- 任务 | 负责人 | 截止日期\n\n## 待跟进事项\n- 未解决的问题和下次讨论计划\n\n保持客观准确，不添加未讨论的内容。",
  "model_id": "anthropic.claude-sonnet-4-20250514",
  "temperature": 0.2,
  "max_tokens": 2048
}
```

### 技术文档写手

```json
{
  "name": "技术文档写手",
  "description": "撰写 API 文档、用户手册、技术博客等技术内容",
  "category": "content_creation",
  "tags": ["文档", "API", "技术写作"],
  "system_prompt": "你是一位技术文档专家。请遵循以下原则:\n1. 使用清晰、准确的语言，避免歧义\n2. 按照受众水平调整技术深度\n3. 使用结构化格式: 标题、列表、代码块、表格\n4. API 文档包含: 端点、参数、响应示例、错误码\n5. 提供实际可运行的代码示例\n6. 包含使用场景和最佳实践\n7. 使用 Markdown 格式输出",
  "model_id": "anthropic.claude-sonnet-4-20250514",
  "temperature": 0.5,
  "max_tokens": 4096
}
```

---

## 附录 B: API 端点速查

| 模块 | 方法 | 端点 | 说明 |
|------|------|------|------|
| **Auth** | POST | `/api/v1/auth/register` | 注册 |
| | POST | `/api/v1/auth/login` | 登录 |
| | POST | `/api/v1/auth/refresh` | 刷新 Token |
| | POST | `/api/v1/auth/logout` | 登出 |
| | GET | `/api/v1/auth/me` | 当前用户信息 |
| **Agents** | POST | `/api/v1/agents` | 创建 Agent |
| | GET | `/api/v1/agents` | Agent 列表 |
| | GET | `/api/v1/agents/:id` | Agent 详情 |
| | PUT | `/api/v1/agents/:id` | 更新 Agent |
| | DELETE | `/api/v1/agents/:id` | 删除 Agent |
| | POST | `/api/v1/agents/:id/activate` | 激活 |
| | POST | `/api/v1/agents/:id/archive` | 归档 |
| | POST | `/api/v1/agents/:id/preview` | 预览测试 |
| **Conversations** | POST | `/api/v1/conversations` | 创建对话 |
| | GET | `/api/v1/conversations` | 对话列表 |
| | GET | `/api/v1/conversations/:id` | 对话详情 |
| | POST | `/api/v1/conversations/:id/messages` | 发送消息 |
| | POST | `/api/v1/conversations/:id/messages/stream` | 流式消息 (SSE) |
| | POST | `/api/v1/conversations/:id/complete` | 结束对话 |
| **Templates** | GET | `/api/v1/templates` | 模板列表 |
| | GET | `/api/v1/templates/:id` | 模板详情 |
| | POST | `/api/v1/templates` | 创建模板 |
| | POST | `/api/v1/templates/:id/publish` | 发布模板 |
| **Insights** | GET | `/api/v1/insights/summary` | 使用概览 |
| | GET | `/api/v1/insights/cost-breakdown` | 成本归因 |
| | GET | `/api/v1/insights/usage-trends` | 使用趋势 |
| | GET | `/api/v1/insights/usage-records` | 使用记录 |
| **Stats** | GET | `/api/v1/stats/summary` | Dashboard 统计 |
| **Health** | GET | `/health` | 存活检查 |
