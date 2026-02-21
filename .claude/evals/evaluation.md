## EVAL: evaluation
Created: 2026-02-18
Updated: 2026-02-21 (新增 EvalPipeline 覆盖)

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

#### EvalPipeline (M13 新增)
- [ ] POST /api/v1/eval-suites/{suite_id}/pipelines 触发 Pipeline 返回 201，初始状态 SCHEDULED
- [ ] GET /api/v1/eval-suites/{suite_id}/pipelines 返回 Pipeline 列表
- [ ] EvalPipeline 实体包含 suite_id, agent_id, trigger, model_ids, status, bedrock_job_id, score_summary, error_message
- [ ] PipelineStatus 枚举: SCHEDULED → RUNNING → COMPLETED / FAILED
- [ ] start() 方法: SCHEDULED → RUNNING (设置 bedrock_job_id)
- [ ] complete() 方法: RUNNING → COMPLETED (设置 score_summary)
- [ ] fail() 方法: RUNNING → FAILED (设置 error_message)
- [ ] 无效状态转换抛出 InvalidStatusTransitionError
- [ ] 同一 suite 不允许同时运行多个 Pipeline (PipelineAlreadyRunningError)
- [ ] EvalPipelineService 调用 IEvalService 接口触发 Bedrock 评估任务
- [ ] BedrockEvalAdapter 使用 asyncio.to_thread 包装 boto3 同步调用
- [ ] BedrockEvalAdapter 封装行数 < 100 行 (SDK-First)
- [ ] BedrockEvalAdapter 精确捕获 ClientError/BotoCoreError (非 Exception)
- [ ] EvalPipelineRepositoryImpl 正确实现 PydanticRepository 多重继承
- [ ] suite_id 路径参数正确传递校验 (套件不存在返回 404)

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
- [ ] EvalPipeline ORM 模型正常 (TEXT 字段无 ORM default)
- [ ] eval_pipelines 表 Alembic 迁移正确执行

#### 状态机
- [ ] TestSuite 状态转换逻辑不变 (DRAFT → ACTIVE → ARCHIVED)
- [ ] EvaluationRun 状态转换逻辑不变 (PENDING → RUNNING → COMPLETED/FAILED)
- [ ] EvalPipeline 状态转换逻辑不变 (SCHEDULED → RUNNING → COMPLETED/FAILED)

#### 跨模块
- [ ] EvalPipeline 不影响现有 TestSuite/EvaluationRun API
- [ ] IEvalService 接口稳定 (外部适配器可替换)

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# 全量评估模块测试
pytest backend/tests/modules/evaluation/ -v --tb=short

# EvalPipeline 专项
pytest backend/tests/modules/evaluation/unit/domain/test_eval_pipeline.py -v
pytest backend/tests/modules/evaluation/unit/domain/test_pipeline_status.py -v
pytest backend/tests/modules/evaluation/unit/application/test_eval_pipeline_service.py -v
pytest backend/tests/modules/evaluation/unit/infrastructure/test_bedrock_eval_adapter.py -v
pytest backend/tests/modules/evaluation/unit/infrastructure/test_eval_pipeline_repository.py -v
pytest backend/tests/modules/evaluation/integration/test_eval_pipeline_endpoints.py -v
```
