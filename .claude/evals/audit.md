## EVAL: audit
Created: 2026-02-18

### Capability Evals

#### API 端点
- [ ] GET /api/v1/audit-logs 返回审计日志列表，支持 category/action/actor_id/resource_type/resource_id/时间范围筛选和分页
- [ ] GET /api/v1/audit-logs/{id} 返回单条审计日志详情
- [ ] GET /api/v1/audit-logs/stats 返回审计统计 (by_category/by_action/total)
- [ ] GET /api/v1/audit-logs/resource/{resource_type}/{resource_id} 按资源查询审计日志
- [ ] GET /api/v1/audit-logs/export 导出审计日志为 CSV (max_rows 默认 10000)

#### 数据模型
- [ ] AuditLog 为 append-only 只读实体 (只写不改不删)
- [ ] 记录完整的请求上下文 (ip_address, user_agent, request_method, request_path, status_code)
- [ ] 记录操作结果 (result, error_message, details)

#### 事件订阅
- [ ] AUTHENTICATION 分类事件正确记录 (登录/登出/注册)
- [ ] AGENT_MANAGEMENT 分类事件正确记录 (Agent CRUD + 状态变更)
- [ ] 其他模块事件正确记录 (工具/知识库/模板/评估等)
- [ ] HTTP 中间件自动记录请求审计

#### 业务规则
- [ ] 所有端点仅 ADMIN 可访问，非 ADMIN 返回 403
- [ ] 按时间范围筛选正确
- [ ] CSV 导出格式正确

#### 认证与权限
- [ ] 未认证请求返回 401
- [ ] 非 ADMIN 返回 403

### Regression Evals

#### 数据库
- [ ] AuditLog ORM 模型正常
- [ ] 审计日志不影响主业务流程性能

#### 事件系统
- [ ] 23 种事件类型订阅正常
- [ ] EventBus 订阅不阻塞主流程

#### 跨模块依赖
- [ ] 审计日志 HTTP 中间件不影响其他中间件链

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
pytest backend/tests/modules/audit/ -v --tb=short
```
