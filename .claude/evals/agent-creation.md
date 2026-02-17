## EVAL: agent-creation
Created: 2026-02-17

### Capability Evals

#### 域实体与状态机
- [ ] Agent 实体创建时默认状态为 DRAFT
- [ ] DRAFT 状态可以激活为 ACTIVE (需 system_prompt 非空)
- [ ] DRAFT/ACTIVE 状态可以归档为 ARCHIVED (不可逆)
- [ ] ARCHIVED 状态不能激活或删除
- [ ] ACTIVE 状态不能被编辑 (除 archive 外)
- [ ] 仅 DRAFT 状态的 Agent 可被删除

#### CRUD API
- [ ] POST /api/v1/agents 创建 Agent 返回 201，默认 DRAFT 状态
- [ ] GET /api/v1/agents 返回当前用户的 Agent 列表，支持状态筛选和分页
- [ ] GET /api/v1/agents/{id} 返回 Agent 详情，非 owner 返回 403/404
- [ ] PUT /api/v1/agents/{id} 仅可更新 DRAFT 状态的 Agent
- [ ] DELETE /api/v1/agents/{id} 仅可删除 DRAFT 状态的 Agent，返回 204

#### 状态转换 API
- [ ] POST /api/v1/agents/{id}/activate 将 DRAFT 转为 ACTIVE，返回 200
- [ ] POST /api/v1/agents/{id}/archive 将 DRAFT/ACTIVE 转为 ARCHIVED，返回 200
- [ ] 无效状态转换返回 409 Conflict

#### 业务规则
- [ ] 同一 owner 下 Agent 名称唯一，重复返回 409
- [ ] 所有操作校验 owner_id == current_user.id (所有权检查)
- [ ] AgentConfig 为 frozen 值对象，更新时整体替换
- [ ] 每个状态变更发布对应 DomainEvent (Created/Updated/Activated/Archived/Deleted)

#### 认证与权限
- [ ] 未认证请求返回 401
- [ ] Agent CRUD 操作需要 DEVELOPER 或 ADMIN 角色

### Regression Evals

#### 共享基础设施
- [ ] PydanticEntity 基类行为正常 (id 生成、时间戳)
- [ ] IRepository 泛型接口合约不变
- [ ] EventBus 事件发布/订阅机制正常
- [ ] DomainError 异常体系映射正确

#### 跨模块契约
- [ ] IAgentQuerier 接口不变 (execution 模块依赖)
- [ ] AgentConfig 值对象序列化/反序列化兼容
- [ ] Agent ACTIVE 状态判定逻辑与 execution 模块一致

#### 数据库
- [ ] Agent ORM 模型与数据库 schema 一致
- [ ] Alembic 迁移可正确执行和回滚

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# 域实体测试
pytest backend/tests/modules/agents/unit/domain/ -v

# 应用服务测试
pytest backend/tests/modules/agents/unit/application/ -v

# API 端点测试
pytest backend/tests/modules/agents/unit/api/ -v
pytest backend/tests/modules/agents/integration/ -v

# 基础设施测试
pytest backend/tests/modules/agents/unit/infrastructure/ -v

# 全量
pytest backend/tests/modules/agents/ -v --tb=short
```
