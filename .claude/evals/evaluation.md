## EVAL: evaluation
Created: 2026-02-18

### Capability Evals

#### 测试集 CRUD
- [ ] POST /api/v1/test-suites 创建测试集返回 201，默认 DRAFT 状态
- [ ] GET /api/v1/test-suites 返回测试集列表，支持分页
- [ ] GET /api/v1/test-suites/{id} 返回测试集详情
- [ ] PUT /api/v1/test-suites/{id} 更新测试集
- [ ] DELETE /api/v1/test-suites/{id} 仅可删除 DRAFT 状态的测试集，返回 204

#### 测试集状态转换
- [ ] POST /api/v1/test-suites/{id}/activate 激活测试集 (DRAFT → ACTIVE)
- [ ] POST /api/v1/test-suites/{id}/archive 归档测试集 (ACTIVE → ARCHIVED)
- [ ] 激活需至少 1 个 TestCase (Service 层校验)
- [ ] 无效状态转换返回 409

#### 测试用例管理
- [ ] POST /api/v1/test-suites/{id}/cases 添加测试用例返回 201
- [ ] GET /api/v1/test-suites/{id}/cases 列出测试用例
- [ ] DELETE /api/v1/test-suites/{id}/cases/{case_id} 删除测试用例返回 204

#### 评估运行
- [ ] POST /api/v1/evaluation-runs 执行评估运行返回 201
- [ ] GET /api/v1/evaluation-runs 返回评估运行列表，支持 suite_id 筛选
- [ ] GET /api/v1/evaluation-runs/{id} 返回评估运行详情
- [ ] GET /api/v1/evaluation-runs/{id}/results 返回评估结果列表
- [ ] EvaluationRun 状态机: PENDING → RUNNING → COMPLETED/FAILED

#### 业务规则
- [ ] 仅 DRAFT 可物理删除
- [ ] 评估结果记录 passed/failed/score
- [ ] owner 鉴权

#### 认证与权限
- [ ] 未认证请求返回 401

### Regression Evals

#### 数据库
- [ ] TestSuite ORM 模型正常
- [ ] TestCase ORM 模型正常
- [ ] EvaluationRun ORM 模型正常
- [ ] EvaluationResult ORM 模型正常

#### 状态机
- [ ] TestSuite 状态转换逻辑不变 (DRAFT → ACTIVE → ARCHIVED)
- [ ] EvaluationRun 状态转换逻辑不变 (PENDING → RUNNING → COMPLETED/FAILED)

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
pytest backend/tests/modules/evaluation/ -v --tb=short
```
