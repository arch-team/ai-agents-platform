# ADR-005: 数据库引擎选型 — 关系库保留 MySQL + RAG 使用 Bedrock Knowledge Bases

- **日期**: 2026-02-10
- **状态**: 已采纳
- **关联**: ADR-002 (技术栈选型), ADR-003 (AgentCore 基础设施), C-S3-1

## 背景

Phase 2 的 knowledge 模块需要向量检索能力（RAG），而当前选用的 Aurora MySQL 不原生支持向量搜索。需要决定是否迁移数据库引擎或引入额外的向量存储方案。

**当前状态**:
- 4 个后端模块 (auth, agents, execution, tool-catalog) 已完成，使用 SQLAlchemy + asyncmy + Aurora MySQL
- 数据库为空（未部署），迁移成本在理论上可控
- CDK 已部署 Aurora MySQL 集群（NetworkStack + SecurityStack + DatabaseStack）
- product-architecture.md 已设计知识库方案为 `S3 + Bedrock Knowledge Base`

## 备选方案

| 方案 | 描述 | 优势 | 劣势 |
|------|------|------|------|
| **A: MySQL + Bedrock Knowledge Bases** | 关系数据保留 MySQL；RAG 向量检索使用 AWS Bedrock Knowledge Bases (全托管) | 零向量存储运维；与 product-architecture 一致；不改现有代码 | 厂商锁定加深；灵活性受限于 Bedrock API |
| **B: MySQL + OpenSearch** | 关系数据保留 MySQL；RAG 使用 Amazon OpenSearch Service 自建向量索引 | OpenSearch 灵活度高；可自定义评分逻辑 | 双数据源同步复杂；新增 CDK Stack + 运维成本 |
| **C: PostgreSQL + pgvector** | 迁移到 Aurora PostgreSQL + pgvector 扩展，单数据源同时处理关系数据和向量检索 | 单数据源简洁；pgvector 成熟；社区生态好 | 需修改所有 4 模块 ORM（asyncmy→asyncpg）；3 个 CDK Stack 需重建；迁移风险 |

## 决策

**选择方案 A: MySQL + Bedrock Knowledge Bases**

## 理由

### 1. 与项目既有设计一致

product-architecture.md 的数据存储策略（§6.2）已明确：
- 业务实体 → MySQL / Aurora MySQL
- 知识库文档 → **S3 + Bedrock Knowledge Base**

方案 A 是对既有架构设计的落地，不引入额外决策。

### 2. 零迁移成本

保留 MySQL 意味着：
- 4 个已完成模块的 ORM、Repository、迁移脚本**零修改**
- 3 个已部署的 CDK Stack 继续使用
- asyncmy 驱动、docker-compose MySQL 8.0 容器、CI 测试基础设施全部保留

### 3. Bedrock Knowledge Bases 的能力匹配

Bedrock Knowledge Bases 提供的全托管 RAG 管道覆盖 knowledge 模块的核心需求：
- **文档摄取**: 支持 S3 数据源，自动分块（Chunking Strategy 可配置）
- **向量化**: 内置 Embedding 模型（Titan Embeddings）或自选模型
- **存储**: 托管的向量存储（OpenSearch Serverless 或 Pinecone 等后端），无需自建
- **检索**: RetrieveAndGenerate API 或 Retrieve API，支持 Hybrid Search（语义 + 关键词）
- **集成**: 与 Bedrock Agent Runtime 原生集成，Phase 3 orchestration 可直接复用

### 4. SDK-First 原则

项目规范（sdk-first.md）要求优先使用 AWS SDK 而非自建。Bedrock Knowledge Bases 是 AWS 原生方案，通过 boto3 SDK 调用，封装 < 100 行即可实现适配器。

### 5. 方案 C 的成本收益不合理

虽然 PostgreSQL + pgvector 技术上更"优雅"（单数据源），但对 200 人的内部平台而言：
- 迁移 4 个模块 + 3 个 CDK Stack 的工程量 > 使用 Bedrock KB 的集成工作量
- pgvector 需要自己管理 Embedding 管道、分块策略、索引调优——Bedrock KB 全托管
- 当前数据库虽为空，但迁移后仍需全面回归测试所有 849 个用例

## 方案 A 的已知局限与缓解

| 局限 | 缓解策略 |
|------|---------|
| Bedrock KB 灵活性受限 | knowledge 模块 Application 层定义 `IKnowledgeService` 接口，未来可替换实现 |
| 厂商锁定加深 | 项目本身基于 Bedrock AgentCore，已处于 AWS 生态，增量锁定有限 |
| Retrieve API 的召回率未知 | M5 验收标准 Top-5 >= 80%，如不达标可评估 Hybrid Search 或降级为方案 B |

## 影响

### knowledge 模块技术选型

| 组件 | 技术方案 |
|------|---------|
| 文档存储 | S3 (原文件) |
| 文档摄取 + 向量化 | Bedrock Knowledge Bases (数据源指向 S3) |
| 向量检索 | Bedrock Retrieve API / RetrieveAndGenerate API |
| 知识库元数据 (名称/描述/状态) | MySQL (与其他模块一致) |
| 适配器 | `infrastructure/external/bedrock_knowledge_adapter.py` (< 100 行) |

### 需要的新 CDK 资源

| 资源 | 说明 |
|------|------|
| S3 Bucket | 知识库文档存储 (KMS 加密, 版本控制) |
| Bedrock Knowledge Base | 全托管 RAG 管道 |
| IAM Role | Bedrock KB 访问 S3 的权限 |

### 对现有代码的影响

**无影响** — 保留 MySQL + asyncmy + 现有 ORM/迁移/CDK。

### ADR-002 状态

ADR-002 (技术栈选型) 保持"已采纳"状态不变。本决策是 ADR-002 的补充，明确了 knowledge 模块的向量存储方案。
