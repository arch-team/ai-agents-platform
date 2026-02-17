## EVAL: templates
Created: 2026-02-18

### Capability Evals

#### CRUD API
- [ ] POST /api/v1/templates 创建模板返回 201，默认 DRAFT 状态
- [ ] GET /api/v1/templates 返回公开已发布模板列表，支持 category/keyword 筛选
- [ ] GET /api/v1/templates/mine 返回当前用户所有模板（含所有状态）
- [ ] GET /api/v1/templates/{id} 返回模板详情
- [ ] PUT /api/v1/templates/{id} 仅可更新 DRAFT 状态的模板
- [ ] DELETE /api/v1/templates/{id} 仅可删除 DRAFT 状态的模板，返回 204

#### 状态转换 API
- [ ] POST /api/v1/templates/{id}/publish 发布模板 (DRAFT → PUBLISHED)
- [ ] POST /api/v1/templates/{id}/archive 归档模板 (PUBLISHED → ARCHIVED)
- [ ] 无效状态转换返回 409

#### 状态机
- [ ] 3 状态流转: DRAFT → PUBLISHED → ARCHIVED
- [ ] PUBLISHED → ARCHIVED 不可逆
- [ ] 仅 DRAFT 可物理删除

#### 业务规则
- [ ] usage_count 自增追踪使用次数
- [ ] 7 分类支持 (customer_service, development 等)
- [ ] owner 鉴权

#### 认证与权限
- [ ] 未认证请求返回 401

### Regression Evals

#### 数据库
- [ ] Template ORM 模型正常
- [ ] 模板配置序列化/反序列化正确

#### 事件系统
- [ ] 模板状态变更发布对应 DomainEvent

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
pytest backend/tests/modules/templates/ -v --tb=short
```
