## EVAL: tool-catalog
Created: 2026-02-18

### Capability Evals

#### CRUD API
- [ ] POST /api/v1/tools 创建工具返回 201，默认 DRAFT 状态
- [ ] GET /api/v1/tools 返回工具列表，支持 status/type/keyword 筛选和分页
- [ ] GET /api/v1/tools/approved 返回已批准工具列表
- [ ] GET /api/v1/tools/{id} 返回工具详情
- [ ] PUT /api/v1/tools/{id} 仅可更新 DRAFT/REJECTED 状态的工具
- [ ] DELETE /api/v1/tools/{id} 仅可删除 DRAFT 状态的工具，返回 204

#### 审批流程 API
- [ ] POST /api/v1/tools/{id}/submit 提交审批 (DRAFT → PENDING_REVIEW)
- [ ] POST /api/v1/tools/{id}/approve 批准工具 (PENDING_REVIEW → APPROVED)，仅 ADMIN
- [ ] POST /api/v1/tools/{id}/reject 拒绝工具 (PENDING_REVIEW → REJECTED)，仅 ADMIN
- [ ] POST /api/v1/tools/{id}/deprecate 废弃工具 (APPROVED → DEPRECATED)

#### 状态机
- [ ] 5 状态流转: DRAFT → PENDING_REVIEW → APPROVED/REJECTED → DEPRECATED
- [ ] REJECTED 可 resubmit 回到 PENDING_REVIEW
- [ ] 无效状态转换返回 409

#### 业务规则
- [ ] 提交审批验证 description 非空
- [ ] MCP_SERVER 类型需 server_url 配置
- [ ] API 类型需 endpoint_url 配置
- [ ] FUNCTION 类型需 runtime + handler 配置
- [ ] 仅 creator 可编辑/删除 DRAFT 工具
- [ ] APPROVED → DEPRECATED 不可逆

#### 认证与权限
- [ ] 未认证请求返回 401
- [ ] 非 ADMIN 不可执行 approve/reject 操作，返回 403

### Regression Evals

#### 跨模块契约
- [ ] IToolQuerier 接口不变 (execution 模块依赖)
- [ ] 已审批工具可被 execution 模块加载为 MCP Server

#### 数据库
- [ ] Tool ORM 模型与数据库 schema 一致
- [ ] 工具配置 JSON 序列化/反序列化正确

#### 事件系统
- [ ] 工具状态变更发布对应 DomainEvent

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
pytest backend/tests/modules/tool_catalog/ -v --tb=short
```
