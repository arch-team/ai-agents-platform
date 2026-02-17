## EVAL: insights
Created: 2026-02-18

### Capability Evals

#### API 端点
- [ ] GET /api/v1/insights/usage-records 返回使用记录列表，支持 user_id/agent_id 筛选
- [ ] GET /api/v1/insights/usage-records/{id} 返回单条记录详情
- [ ] GET /api/v1/insights/summary 返回概览统计，支持时间范围参数
- [ ] GET /api/v1/insights/cost-breakdown 返回按 Agent 维度的 Token 归因
- [ ] GET /api/v1/insights/usage-trends 返回按日维度的使用趋势

#### 数据模型
- [ ] UsageRecord 为只读 append-only 实体
- [ ] total_tokens 计算属性 = tokens_input + tokens_output
- [ ] estimated_cost 正确计算

#### 业务规则
- [ ] 非 ADMIN 用户只能查看自己的数据
- [ ] ADMIN 可查看全部数据
- [ ] 时间范围默认最近 30 天
- [ ] Cost Explorer 集成正确返回平台总成本

#### 事件订阅
- [ ] MessageReceivedEvent 触发 UsageRecord 创建
- [ ] Token 消耗正确记录 input/output 分项

#### 认证与权限
- [ ] 未认证请求返回 401

### Regression Evals

#### 数据库
- [ ] UsageRecord ORM 模型正常
- [ ] 按时间范围查询性能正常

#### 跨模块依赖
- [ ] EventBus 事件订阅不影响 execution 主流程
- [ ] CostExplorerAdapter 接口稳定

#### 统计计算
- [ ] cost-breakdown 聚合结果正确
- [ ] usage-trends 日维度聚合正确

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
pytest backend/tests/modules/insights/ -v --tb=short
```
