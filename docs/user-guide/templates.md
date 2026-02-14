# 模板使用指南

> 本指南说明如何浏览预置模板、从模板创建 Agent，以及发布自定义模板。

---

## 目录

- [模板概述](#模板概述)
- [模板分类](#模板分类)
- [浏览预置模板](#浏览预置模板)
- [从模板创建 Agent](#从模板创建-agent)
- [创建自定义模板](#创建自定义模板)
- [发布模板](#发布模板)
- [管理模板](#管理模板)
- [API 参考](#api-参考)
- [常见问题](#常见问题)

---

## 模板概述

模板 (Template) 是预配置的 Agent 方案，包含 System Prompt、模型选择和参数配置。通过模板，非技术人员也能快速创建专业的 AI Agent。

平台提供 **10 个预置模板**，覆盖 7 种常见业务场景。用户也可以将自己配置好的 Agent 发布为模板供他人使用。

### 模板生命周期

```
DRAFT (草稿) ──发布──> PUBLISHED (已发布) ──归档──> ARCHIVED (已归档)
```

| 状态 | 说明 | 可见范围 |
|------|------|---------|
| **DRAFT** | 草稿状态，可编辑 | 仅创建者 |
| **PUBLISHED** | 已发布，可被其他用户使用 | 所有用户 |
| **ARCHIVED** | 已归档，不再展示 | 仅创建者 |

---

## 模板分类

| 分类 | 英文标识 | 说明 | 典型场景 |
|------|---------|------|---------|
| 客户服务 | customer_service | 客户咨询和支持 | 产品咨询、故障排查、投诉处理 |
| 代码助手 | code_assistant | 编程和技术支持 | 代码审查、Bug 分析、技术问答 |
| 数据分析 | data_analysis | 数据处理和分析 | 报表生成、数据洞察、趋势分析 |
| 内容创作 | content_creation | 文本生成和编辑 | 文案写作、邮件起草、翻译 |
| 研究助手 | research | 信息检索和研究 | 文献调研、竞品分析、市场研究 |
| 工作流自动化 | workflow_automation | 流程自动化 | 审批流程、数据搬运、定期报告 |
| 通用 | general | 通用场景 | 日常对话、问答、学习辅助 |

---

## 浏览预置模板

### 前端操作

1. 导航到 **模板** 页面
2. 查看模板列表，默认显示所有已发布的模板
3. 使用分类筛选或关键词搜索定位目标模板
4. 点击模板卡片查看详情

### API 调用

**列出已发布模板**:

```
GET /api/v1/templates?page=1&page_size=20
```

**按分类筛选**:

```
GET /api/v1/templates?category=customer_service
```

**关键词搜索**:

```
GET /api/v1/templates?keyword=客服
```

---

## 从模板创建 Agent

### 操作步骤

1. 在模板列表中找到目标模板
2. 点击 **使用此模板** 按钮
3. 模板的配置（System Prompt、模型参数）自动填入创建 Agent 表单
4. 根据需要修改 Agent 名称和配置
5. 点击 **创建** 完成

### 流程说明

从模板创建 Agent 本质上是复制模板的配置到新 Agent，创建后的 Agent 与模板无关联，可以自由修改。

```
查看模板详情 ──> 复制配置到创建表单 ──> 自定义修改 ──> 创建 Agent
```

### API 流程

1. 获取模板详情:

```
GET /api/v1/templates/{template_id}
```

2. 使用模板配置创建 Agent:

```
POST /api/v1/agents
Content-Type: application/json

{
  "name": "我的客服助手",
  "description": "基于客服模板创建",
  "system_prompt": "<从模板复制>",
  "model_id": "<从模板复制>",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

---

## 创建自定义模板

DEVELOPER 和 ADMIN 角色可以创建自定义模板。

### 步骤

1. 导航到 **模板** 页面
2. 点击 **创建模板** 按钮
3. 填写模板信息:

| 字段 | 说明 | 必填 |
|------|------|:----:|
| name | 模板名称 (全局唯一) | Y |
| description | 模板描述 | Y |
| category | 分类 (7 选 1) | Y |
| system_prompt | System Prompt 模板 | Y |
| model_id | 推荐模型 | N |
| temperature | 推荐温度 | N |
| max_tokens | 推荐 max_tokens | N |

### API 调用

```
POST /api/v1/templates
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "技术支持 Agent",
  "description": "专为技术支持场景设计的 Agent 模板",
  "category": "customer_service",
  "system_prompt": "你是一个技术支持工程师，负责帮助用户解决技术问题...",
  "model_id": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
  "temperature": 0.3,
  "max_tokens": 4096
}
```

---

## 发布模板

创建的模板默认为 DRAFT 状态，发布后才能被其他用户看到和使用。

### 操作

```
POST /api/v1/templates/{template_id}/publish
Authorization: Bearer <access_token>
```

发布条件:

- 模板状态为 DRAFT
- 名称、描述、分类、System Prompt 均已填写

---

## 管理模板

### 查看我的模板

```
GET /api/v1/templates/mine
```

返回当前用户创建的所有模板（含所有状态）。

### 编辑模板

仅 DRAFT 状态的模板可编辑:

```
PUT /api/v1/templates/{template_id}
Content-Type: application/json

{
  "description": "更新后的描述",
  "system_prompt": "优化后的 System Prompt..."
}
```

### 归档模板

将已发布的模板下线:

```
POST /api/v1/templates/{template_id}/archive
```

归档后模板不再出现在公开列表中。

### 删除模板

仅 DRAFT 状态的模板可删除:

```
DELETE /api/v1/templates/{template_id}
```

---

## API 参考

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/templates` | 创建模板 | DEVELOPER+ |
| GET | `/api/v1/templates` | 已发布模板列表 | 所有认证用户 |
| GET | `/api/v1/templates/mine` | 我的模板列表 | DEVELOPER+ |
| GET | `/api/v1/templates/{id}` | 模板详情 | 所有认证用户 |
| PUT | `/api/v1/templates/{id}` | 更新模板 (DRAFT) | 创建者 |
| DELETE | `/api/v1/templates/{id}` | 删除模板 (DRAFT) | 创建者 |
| POST | `/api/v1/templates/{id}/publish` | 发布模板 | 创建者 |
| POST | `/api/v1/templates/{id}/archive` | 归档模板 | 创建者 |

### 列表查询参数

| 参数 | 说明 | 示例 |
|------|------|------|
| category | 按分类筛选 | `?category=code_assistant` |
| keyword | 关键词搜索 | `?keyword=客服` |
| page | 页码 | `?page=1` |
| page_size | 每页数量 | `?page_size=20` |

---

## 常见问题

### Q1: 预置模板可以修改吗？

预置模板本身不可修改。但你可以从预置模板创建 Agent 后，在 Agent 层面自由修改所有配置。

### Q2: 我发布的模板别人修改后会影响我的原始模板吗？

不会。从模板创建的 Agent 是独立的副本，对 Agent 的修改不会影响模板本身。

### Q3: 模板归档后已经使用该模板创建的 Agent 会受影响吗？

不会。模板归档仅影响模板在公开列表中的展示。已创建的 Agent 是独立实体，不受模板状态影响。

### Q4: 如何编写好的 System Prompt？

编写 System Prompt 的建议:

1. **明确角色**: 开头说明 Agent 的身份和职责
2. **设定规则**: 列出行为规范和限制条件
3. **给出示例**: 提供期望的回答示例
4. **控制格式**: 指定输出格式（如列表、表格、段落）
5. **设定边界**: 明确不应该回答的问题类型

### Q5: 模板可以包含工具和知识库配置吗？

当前版本模板仅包含 System Prompt 和模型参数配置。工具和知识库需要在创建 Agent 后单独配置。
