## EVAL: cross-module-integration
Created: 2026-02-21

### Capability Evals

#### 端到端业务流程: 注册 → 创建 Agent → 对话
- [ ] 用户注册 → 登录获取 JWT → 创建 Agent → 激活 → 创建对话 → 发送消息 → 收到回复
- [ ] SSE 流式对话: 创建对话 → stream 端点 → 接收多个 SSE chunk → 完整回复
- [ ] 对话完成: 发送消息 → 回复 → complete 对话 → 状态变为 COMPLETED

#### 端到端业务流程: Agent Teams
- [ ] 创建 Agent (enable_teams=True) → 激活 → 提交 Team Execution → 后台执行 → 查看日志/结果
- [ ] SSE 进度推送: 提交执行 → stream 端点 → 实时接收日志 → 执行完成
- [ ] 取消执行: 提交执行 → PENDING/RUNNING 状态 → cancel → CANCELLED

#### 端到端业务流程: 工具注册 → 审批 → Agent 使用
- [ ] 创建工具 (DRAFT) → submit 审批 → ADMIN approve → 工具变为 APPROVED
- [ ] APPROVED 工具通过 IToolQuerier 可被 execution 模块发现
- [ ] Agent 执行时自动加载关联的已审批工具
- [ ] Gateway 同步: 工具审批通过 → DomainEvent → GatewaySyncAdapter 注册

#### 端到端业务流程: 知识库 → RAG 检索 → Agent 对话
- [ ] 创建知识库 → 上传文档 → 同步索引 → 关联 Agent
- [ ] Agent 对话时自动检索关联知识库 → RAG 上下文注入 LLM
- [ ] 知识库删除不影响已完成的对话记录

#### 端到端业务流程: 模板 → 创建 Agent
- [ ] 发布模板 → 使用模板配置创建 Agent → Agent 继承模板的 system_prompt/model_id/temperature
- [ ] 模板 usage_count 在被使用时自增

#### 端到端业务流程: 评估
- [ ] 创建测试集 → 添加测试用例 → 激活 → 执行评估运行 → 查看结果
- [ ] EvalPipeline: 激活测试集 → 触发 Pipeline → Bedrock 评估 → 完成/失败

#### 跨模块事件驱动
- [ ] Agent 创建 → AgentCreatedEvent → audit 模块记录审计日志
- [ ] 消息接收 → MessageReceivedEvent → insights 模块记录 UsageRecord
- [ ] 团队执行完成 → TeamExecutionCompletedEvent → insights 模块记录成本
- [ ] 对话完成 → ConversationCompletedEvent → Memory 模块提取记忆
- [ ] 工具审批 → ToolApprovedEvent → Gateway 模块同步注册
- [ ] 工具废弃 → ToolDeprecatedEvent → Gateway 模块同步注销

#### 跨模块查询接口
- [ ] IAgentQuerier: execution 查询 agents 模块 → 返回 ActiveAgentInfo
- [ ] IToolQuerier: execution 查询 tool_catalog 模块 → 返回已审批工具列表
- [ ] IKnowledgeQuerier: execution 查询 knowledge 模块 → 返回知识库信息
- [ ] 查询接口在目标模块不可用时优雅降级 (非崩溃)

#### RBAC 跨模块一致性
- [ ] ADMIN 可操作所有模块的所有资源
- [ ] DEVELOPER 可创建 Agent/工具/模板/知识库/测试集
- [ ] VIEWER 只能查看公开资源 (已发布模板、已审批工具)
- [ ] 未认证用户仅可访问 /health 和 /auth 端点

#### 统计端点跨模块聚合
- [ ] GET /api/v1/stats/summary 正确聚合 agents/conversations/team_executions 计数
- [ ] ADMIN 看全局统计，普通用户看自己的统计

#### Insights 数据一致性
- [ ] 普通对话的 token 消耗正确记录到 UsageRecord
- [ ] 团队执行的 token 消耗正确记录到 UsageRecord
- [ ] cost-breakdown 聚合结果与 UsageRecord 明细一致
- [ ] usage-trends 日维度聚合与实际使用一致

### Regression Evals

#### 模块边界
- [ ] 模块间仅通过 EventBus + Querier 接口通信 (无直接 import)
- [ ] 各模块可独立启动测试 (无隐式依赖)

#### 数据一致性
- [ ] 事件驱动的数据最终一致 (审计/Insights)
- [ ] EventBus 订阅者异常不影响主业务流程
- [ ] 跨模块查询失败不导致主流程中断

#### API 一致性
- [ ] 所有端点统一使用 /api/v1/ 前缀
- [ ] 错误响应格式统一 {"code", "message", "details"}
- [ ] 分页参数统一 (page, page_size)

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# E2E 后端测试
pytest backend/tests/e2e/ -v --tb=short

# 架构合规测试 (模块边界)
pytest backend/tests/test_architecture_compliance.py -v

# 事件订阅集成
pytest backend/tests/presentation/ -v

# 前端 E2E (完整用户旅程)
cd frontend && npx playwright test tests/e2e/ --reporter=list

# 全量后端测试 (检测跨模块回归)
pytest backend/tests/ -v --tb=short -x
```
