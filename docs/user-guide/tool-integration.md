# 工具集成指南

> 本指南说明如何注册和管理 Agent 可使用的外部工具，以及工具审批流程。

---

## 目录

- [工具概述](#工具概述)
- [工具类型](#工具类型)
- [工具审批流程](#工具审批流程)
- [注册工具](#注册工具)
- [提交审批](#提交审批)
- [工具配置示例](#工具配置示例)
- [与 Agent 关联](#与-agent-关联)
- [API 参考](#api-参考)
- [常见问题](#常见问题)

---

## 工具概述

工具 (Tool) 赋予 Agent 调用外部服务的能力。例如，一个客服 Agent 可以通过工具查询订单系统，一个数据分析 Agent 可以通过工具执行 SQL 查询。

平台支持三种工具类型，覆盖主流集成场景。所有工具需经过 ADMIN 审批后才能被 Agent 使用。

---

## 工具类型

### MCP Server

Model Context Protocol (MCP) 服务器是标准化的工具协议，Agent 通过 MCP 协议与工具通信。

| 配置项 | 说明 | 示例 |
|--------|------|------|
| server_url | MCP Server 地址 | `https://tools.example.com/mcp` |
| transport | 传输协议 | `sse` 或 `stdio` |

**适用场景**: 已实现 MCP 协议的服务、第三方 MCP 工具。

### API

直接调用 REST API 端点，适用于已有的内部微服务。

| 配置项 | 说明 | 示例 |
|--------|------|------|
| endpoint_url | API 端点地址 | `https://api.example.com/orders` |
| method | HTTP 方法 | `GET`、`POST` |
| auth_type | 认证方式 | `bearer`、`api_key` |

**适用场景**: 内部 REST API、第三方 SaaS API。

### Function

自定义函数，直接在 Agent 运行时执行代码。

| 配置项 | 说明 | 示例 |
|--------|------|------|
| runtime | 运行时环境 | `python3.11` |
| handler | 入口函数 | `handler.main` |
| code_uri | 代码包地址 | `s3://tools-bucket/func.zip` |

**适用场景**: 自定义业务逻辑、数据转换处理。

---

## 工具审批流程

工具从注册到可用需要经过审批流程:

```
DRAFT (草稿) ──提交──> PENDING_REVIEW (待审批)
                           │
                  ┌────────┼────────┐
                  v                 v
          APPROVED (已批准)   REJECTED (已拒绝)
              │                     │
              v                     v
     DEPRECATED (已废弃)    PENDING_REVIEW (重新提交)
```

| 状态 | 说明 | 可执行操作 |
|------|------|----------|
| **DRAFT** | 新注册的工具 | 编辑、提交审批、删除 |
| **PENDING_REVIEW** | 等待 ADMIN 审批 | (等待中) |
| **APPROVED** | 审批通过，Agent 可使用 | 废弃 |
| **REJECTED** | 审批被拒绝 | 编辑、重新提交 |
| **DEPRECATED** | 已废弃，不可逆 | 仅查看 |

---

## 注册工具

### 步骤

1. 导航到 **工具目录** 页面
2. 点击 **注册工具** 按钮
3. 填写工具信息和配置

### 基本信息

| 字段 | 说明 | 必填 |
|------|------|:----:|
| name | 工具名称 (同一创建者下唯一) | Y |
| description | 工具功能描述 | Y |
| tool_type | 工具类型: MCP_SERVER / API / FUNCTION | Y |
| version | 版本号 | N |

### API 调用

```
POST /api/v1/tools
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "订单查询工具",
  "description": "根据订单号查询订单状态和详情",
  "tool_type": "API",
  "version": "1.0",
  "endpoint_url": "https://api.internal.com/orders",
  "method": "GET",
  "auth_type": "bearer"
}
```

---

## 提交审批

工具配置完成后，需要提交给 ADMIN 审批。

### 提交条件

- 名称不为空
- 描述不为空
- 工具配置完整（对应类型的必填字段已填写）

### 操作

```
POST /api/v1/tools/{tool_id}/submit
Authorization: Bearer <access_token>
```

提交后状态变为 PENDING_REVIEW，等待 ADMIN 审批。

### 审批被拒绝后

如果工具被拒绝，可以:

1. 查看审批人的拒绝原因 (review_comment 字段)
2. 修改工具配置
3. 重新提交审批

```
PUT /api/v1/tools/{tool_id}
Content-Type: application/json

{
  "description": "根据订单号查询订单状态和详情（已增加权限校验）",
  "auth_type": "bearer"
}
```

然后重新提交:

```
POST /api/v1/tools/{tool_id}/submit
```

---

## 工具配置示例

### MCP Server 示例

```json
{
  "name": "文件管理工具",
  "description": "读取和搜索项目文件",
  "tool_type": "MCP_SERVER",
  "server_url": "https://mcp.internal.com/filesystem",
  "transport": "sse"
}
```

### API 示例

```json
{
  "name": "天气查询",
  "description": "根据城市名称查询实时天气信息",
  "tool_type": "API",
  "version": "2.0",
  "endpoint_url": "https://api.weather.com/v2/current",
  "method": "GET",
  "auth_type": "api_key"
}
```

### Function 示例

```json
{
  "name": "数据格式转换",
  "description": "将 CSV 数据转换为 JSON 格式",
  "tool_type": "FUNCTION",
  "runtime": "python3.11",
  "handler": "converter.csv_to_json",
  "code_uri": "s3://ai-agents-tools/converters/csv_to_json.zip"
}
```

---

## 与 Agent 关联

已批准 (APPROVED) 的工具可以在 Agent 创建或更新时关联。Agent 在执行对话时会自动获取关联的工具能力。

### 查看已批准工具

```
GET /api/v1/tools/approved
```

此端点返回所有已批准的工具列表，所有认证用户均可访问。

---

## API 参考

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/tools` | 注册工具 | DEVELOPER+ |
| GET | `/api/v1/tools` | 工具列表 (支持筛选) | DEVELOPER+ |
| GET | `/api/v1/tools/approved` | 已批准工具列表 | 所有认证用户 |
| GET | `/api/v1/tools/{id}` | 工具详情 | DEVELOPER+ |
| PUT | `/api/v1/tools/{id}` | 更新工具 (DRAFT/REJECTED) | 创建者 |
| DELETE | `/api/v1/tools/{id}` | 删除工具 (DRAFT) | 创建者 |
| POST | `/api/v1/tools/{id}/submit` | 提交审批 | 创建者 |
| POST | `/api/v1/tools/{id}/approve` | 审批通过 | ADMIN |
| POST | `/api/v1/tools/{id}/reject` | 审批拒绝 | ADMIN |
| POST | `/api/v1/tools/{id}/deprecate` | 废弃工具 | 创建者/ADMIN |

### 列表筛选参数

| 参数 | 说明 | 示例 |
|------|------|------|
| status | 按状态筛选 | `?status=approved` |
| type | 按类型筛选 | `?type=API` |
| keyword | 关键词搜索 (名称/描述) | `?keyword=订单` |
| page | 页码 (从 1 开始) | `?page=1` |
| page_size | 每页数量 (最大 100) | `?page_size=20` |

---

## 常见问题

### Q1: 工具审批需要多长时间？

审批由 ADMIN 角色人工处理。建议在提交审批后通过内部沟通渠道通知管理员。

### Q2: 工具废弃后已关联的 Agent 怎么办？

工具废弃后，已关联该工具的 Agent 在后续对话中将无法调用该工具。建议在废弃前通知相关 Agent 的所有者，替换为新的工具。

### Q3: 如何选择工具类型？

| 场景 | 推荐类型 |
|------|---------|
| 已有 MCP 协议实现的服务 | MCP_SERVER |
| 调用现有 REST API | API |
| 需要自定义处理逻辑 | FUNCTION |
| 不确定 | 优先考虑 API，覆盖范围最广 |

### Q4: 工具的认证信息如何安全存储？

工具的认证配置（如 API Key）通过 AgentCore Gateway 安全管理，不会直接存储在平台数据库中。Token Vault 功能可进一步增强第三方 API Key 的安全管理。
