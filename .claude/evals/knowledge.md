## EVAL: knowledge
Created: 2026-02-18

### Capability Evals

#### 知识库 CRUD
- [ ] POST /api/v1/knowledge-bases 创建知识库返回 201，初始状态 CREATING
- [ ] GET /api/v1/knowledge-bases 返回知识库列表，支持分页
- [ ] GET /api/v1/knowledge-bases/{id} 返回知识库详情
- [ ] PUT /api/v1/knowledge-bases/{id} 更新知识库
- [ ] DELETE /api/v1/knowledge-bases/{id} 删除知识库，仅 ACTIVE/FAILED 可删除，返回 204

#### 文档管理
- [ ] POST /api/v1/knowledge-bases/{id}/documents 上传文档返回 201
- [ ] GET /api/v1/knowledge-bases/{id}/documents 返回文档列表
- [ ] DELETE /api/v1/knowledge-bases/{id}/documents/{doc_id} 删除文档返回 204

#### 同步与检索
- [ ] POST /api/v1/knowledge-bases/{id}/sync 手动同步返回 200
- [ ] POST /api/v1/knowledge-bases/{id}/query RAG 检索返回 200

#### 状态机
- [ ] CREATING → ACTIVE (激活)
- [ ] ACTIVE ⇄ SYNCING (同步)
- [ ] CREATING/SYNCING → FAILED (失败)
- [ ] ACTIVE/FAILED → DELETED (删除)
- [ ] 无效状态转换返回 409

#### 业务规则
- [ ] 仅 owner 可操作自己的知识库
- [ ] 仅 ACTIVE/FAILED 状态可删除
- [ ] CREATING/SYNCING 状态可转为 FAILED

#### 认证与权限
- [ ] 未认证请求返回 401

### Regression Evals

#### 跨模块契约
- [ ] RAG 上下文注入在 execution 模块中正常工作
- [ ] Bedrock Knowledge Bases 适配器接口稳定

#### 数据库
- [ ] KnowledgeBase ORM 模型正常
- [ ] Document ORM 模型正常

#### 事件系统
- [ ] 知识库状态变更发布对应 DomainEvent

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
pytest backend/tests/modules/knowledge/ -v --tb=short
```
