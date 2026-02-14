# 知识库使用指南

> 本指南说明如何创建知识库、上传文档、执行 RAG 检索，以及将知识库与 Agent 关联。

---

## 目录

- [知识库概述](#知识库概述)
- [RAG 检索原理](#rag-检索原理)
- [创建知识库](#创建知识库)
- [上传文档](#上传文档)
- [同步知识库](#同步知识库)
- [RAG 检索测试](#rag-检索测试)
- [与 Agent 关联](#与-agent-关联)
- [管理知识库](#管理知识库)
- [API 参考](#api-参考)
- [常见问题](#常见问题)

---

## 知识库概述

知识库 (Knowledge Base) 允许你上传企业文档，让 Agent 基于真实的企业知识回答问题，而非仅依赖 AI 模型的预训练知识。

**核心组件**:

- **知识库**: 文档集合的逻辑容器
- **文档**: 上传到知识库的文件（PDF、TXT、Markdown 等）
- **RAG 检索**: 将用户问题与文档内容进行语义匹配，返回相关片段

**技术实现**: 基于 Amazon Bedrock Knowledge Bases，文档存储在 S3，向量索引由 Bedrock 全托管。

---

## RAG 检索原理

RAG (Retrieval-Augmented Generation) 检索增强生成的工作流程:

```
用户提问 ──> 语义搜索知识库 ──> 返回相关文档片段
                                      │
                                      v
用户提问 + 相关文档片段 ──> LLM 生成回答 ──> 返回用户
```

1. **文档预处理**: 上传的文档被分块 (chunking)，每个块生成向量嵌入
2. **语义搜索**: 用户提问转为向量，在知识库中检索语义最相关的文档块
3. **上下文注入**: 检索到的文档片段作为额外上下文注入 LLM 提示
4. **生成回答**: LLM 基于用户问题和文档上下文生成准确回答

**优势**: Agent 的回答基于实际的企业文档，减少"幻觉"，提升准确性。

---

## 创建知识库

### 步骤

1. 导航到 **知识库** 页面
2. 点击 **创建知识库** 按钮
3. 填写信息:

| 字段 | 说明 | 必填 |
|------|------|:----:|
| name | 知识库名称 (同一用户下唯一) | Y |
| description | 知识库描述 | N |
| agent_id | 关联的 Agent ID (可选，后续也可关联) | N |

### API 调用

```
POST /api/v1/knowledge-bases
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "产品使用手册",
  "description": "包含所有产品的用户使用手册和技术文档"
}
```

**响应** (201 Created):

```json
{
  "id": 1,
  "name": "产品使用手册",
  "description": "包含所有产品的用户使用手册和技术文档",
  "status": "creating",
  "owner_id": 1,
  "agent_id": null,
  "bedrock_kb_id": "KB-xxx",
  "s3_prefix": "knowledge-bases/1/",
  "created_at": "2026-02-14T10:00:00",
  "updated_at": "2026-02-14T10:00:00"
}
```

### 知识库状态

| 状态 | 说明 |
|------|------|
| CREATING | 正在创建 Bedrock Knowledge Base 资源 |
| ACTIVE | 创建完成，可上传文档和检索 |
| SYNCING | 正在同步文档索引 |
| FAILED | 创建或同步失败 |
| DELETED | 已删除 |

---

## 上传文档

### 支持的文件类型

- PDF 文档 (.pdf)
- 纯文本 (.txt)
- Markdown (.md)
- HTML (.html)
- Microsoft Word (.docx)
- CSV (.csv)

### 上传步骤

1. 进入知识库详情页
2. 点击 **上传文档** 按钮
3. 选择或拖拽文件
4. 等待上传完成

### API 调用

```
POST /api/v1/knowledge-bases/{kb_id}/documents
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <文件内容>
```

**响应** (201 Created):

```json
{
  "id": 1,
  "knowledge_base_id": 1,
  "filename": "user-guide.pdf",
  "s3_key": "knowledge-bases/1/user-guide.pdf",
  "file_size": 1048576,
  "status": "uploading",
  "content_type": "application/pdf",
  "chunk_count": 0,
  "created_at": "2026-02-14T10:05:00",
  "updated_at": "2026-02-14T10:05:00"
}
```

### 文档处理状态

| 状态 | 说明 |
|------|------|
| UPLOADING | 正在上传到 S3 |
| PROCESSING | Bedrock 正在处理和分块 |
| INDEXED | 索引完成，可用于检索 |
| FAILED | 处理失败 |

文档上传后需要经过 Bedrock 异步处理才能用于检索，通常需要几分钟。

---

## 同步知识库

上传新文档或删除文档后，需要触发同步以更新索引。

### 操作

```
POST /api/v1/knowledge-bases/{kb_id}/sync
Authorization: Bearer <access_token>
```

同步是异步操作，知识库状态会暂时变为 SYNCING，完成后恢复为 ACTIVE。

---

## RAG 检索测试

可以直接测试知识库的检索效果，验证文档索引质量。

### 操作

```
POST /api/v1/knowledge-bases/{kb_id}/query
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "query": "如何重置密码？",
  "top_k": 5
}
```

**参数说明**:

| 参数 | 说明 | 默认值 |
|------|------|--------|
| query | 检索问题 | (必填) |
| top_k | 返回最相关的文档数量 | 5 |

**响应**:

```json
{
  "query": "如何重置密码？",
  "knowledge_base_id": 1,
  "results": [
    {
      "content": "重置密码的步骤：1. 点击登录页面的'忘记密码'...",
      "score": 0.92,
      "document_id": "doc-xxx",
      "metadata": {}
    },
    {
      "content": "账户安全设置：建议定期更换密码...",
      "score": 0.85,
      "document_id": "doc-yyy",
      "metadata": {}
    }
  ]
}
```

**score** 字段表示语义相关性分数 (0-1)，越高越相关。

---

## 与 Agent 关联

将知识库关联到 Agent 后，Agent 在对话时会自动检索相关文档，将结果作为上下文注入 LLM。

### 关联方式

**方式一**: 创建知识库时指定 agent_id

```json
{
  "name": "客服知识库",
  "agent_id": 1
}
```

**方式二**: 更新知识库关联

```
PUT /api/v1/knowledge-bases/{kb_id}
Content-Type: application/json

{
  "agent_id": 1
}
```

### 对话时的自动检索

关联后，用户与 Agent 对话时:

1. 用户发送消息
2. 系统自动在关联的知识库中检索相关内容
3. 检索结果作为上下文注入到 Agent 的 System Prompt 中
4. Agent 基于用户问题和知识库内容生成回答

这个过程对用户完全透明，无需手动触发检索。

---

## 管理知识库

### 查看文档列表

```
GET /api/v1/knowledge-bases/{kb_id}/documents?page=1&page_size=20
```

### 删除文档

```
DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}
```

删除文档后建议执行一次同步以更新索引。

### 更新知识库信息

```
PUT /api/v1/knowledge-bases/{kb_id}
Content-Type: application/json

{
  "name": "产品手册 v2",
  "description": "更新后的产品文档集合"
}
```

### 删除知识库

```
DELETE /api/v1/knowledge-bases/{kb_id}
```

删除知识库会同时删除所有关联文档和 Bedrock Knowledge Base 资源。

---

## API 参考

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/knowledge-bases` | 创建知识库 |
| GET | `/api/v1/knowledge-bases` | 知识库列表 |
| GET | `/api/v1/knowledge-bases/{id}` | 知识库详情 |
| PUT | `/api/v1/knowledge-bases/{id}` | 更新知识库 |
| DELETE | `/api/v1/knowledge-bases/{id}` | 删除知识库 |
| POST | `/api/v1/knowledge-bases/{id}/documents` | 上传文档 |
| GET | `/api/v1/knowledge-bases/{id}/documents` | 文档列表 |
| DELETE | `/api/v1/knowledge-bases/{id}/documents/{doc_id}` | 删除文档 |
| POST | `/api/v1/knowledge-bases/{id}/sync` | 同步知识库 |
| POST | `/api/v1/knowledge-bases/{id}/query` | RAG 检索 |

---

## 常见问题

### Q1: 上传文档后多久可以检索到？

文档上传后需要 Bedrock 异步处理（分块、向量化、索引），通常需要 2-5 分钟。大文档可能需要更长时间。文档状态变为 INDEXED 后即可检索。

### Q2: 检索结果不准确怎么办？

可以尝试以下方法:

1. **优化文档质量**: 确保文档内容清晰、结构化
2. **调整 top_k**: 增加返回结果数量可提升覆盖率
3. **细化问题**: 使用更具体的关键词
4. **手动同步**: 上传新文档后执行同步操作

### Q3: 一个知识库可以关联多个 Agent 吗？

知识库的 agent_id 字段指向一个 Agent，但多个 Agent 可以通过各自的知识库引用相同类型的文档。在 Agent 对话时，系统会检索该 Agent 关联的所有知识库。

### Q4: 支持的最大文件大小是多少？

文件大小受 S3 上传限制和服务端配置约束。建议单个文件不超过 50MB。如果文档过大，建议拆分为多个较小的文件上传。

### Q5: 删除文档后需要重新同步吗？

建议是的。删除文档后执行一次同步 (`POST /knowledge-bases/{id}/sync`) 可以确保索引及时更新，避免检索到已删除的内容。
