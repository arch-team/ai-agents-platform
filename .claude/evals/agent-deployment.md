## EVAL: agent-deployment
Created: 2026-02-17

### Capability Evals

#### 对话管理
- [ ] POST /api/v1/conversations 创建对话，校验 Agent 处于 ACTIVE 状态，返回 201
- [ ] GET /api/v1/conversations 返回用户对话列表，支持 agent_id 筛选和分页
- [ ] GET /api/v1/conversations/{id} 返回对话详情含消息历史
- [ ] POST /api/v1/conversations/{id}/complete 结束对话，返回 200
- [ ] 对话状态机: ACTIVE -> COMPLETED / FAILED

#### 消息发送
- [ ] POST /api/v1/conversations/{id}/messages 同步发送消息，返回 201
- [ ] POST /api/v1/conversations/{id}/messages/stream 流式发送消息 (SSE)，返回 200
- [ ] 仅 ACTIVE 对话可发送消息
- [ ] 消息历史滑动窗口截取正常工作

#### 运行时路由
- [ ] runtime_type == "agent" 且有 agent_runtime 时路由到 ClaudeAgentAdapter
- [ ] 无 agent_runtime 时降级到 ILLMClient (Bedrock Converse API)
- [ ] ClaudeAgentAdapter 正确调用 claude_agent_sdk.query()
- [ ] AgentCoreRuntimeAdapter 正确调用 bedrock invoke_inline_agent

#### 团队执行
- [ ] POST /api/v1/team-executions 提交团队执行任务，返回 201
- [ ] GET /api/v1/team-executions 返回用户团队执行列表
- [ ] GET /api/v1/team-executions/{id} 返回执行详情
- [ ] GET /api/v1/team-executions/{id}/logs 返回执行日志 (支持增量查询)
- [ ] GET /api/v1/team-executions/{id}/stream SSE 进度推送
- [ ] POST /api/v1/team-executions/{id}/cancel 取消团队执行
- [ ] 团队执行状态机: PENDING -> RUNNING -> COMPLETED / FAILED / CANCELLED

#### Agent 预览
- [ ] POST /api/v1/agents/{id}/preview 单轮测试不持久化，返回 200

#### 安全
- [ ] SSRF 防护: ClaudeAgentAdapter 阻止访问内部/私有 IP 地址
- [ ] 所有操作校验对话 user_id == current_user.id

#### 工具与知识库集成
- [ ] 通过 IToolQuerier 加载已审批工具并封装为 MCP Server
- [ ] RAG 上下文注入 (知识库) 正常工作
- [ ] 长期记忆注入正常工作

#### 事件与指标
- [ ] Token 消耗通过 MessageReceivedEvent 记录到 insights 模块
- [ ] 团队执行成本归因事件正确发布

### Regression Evals

#### 跨模块依赖
- [ ] IAgentQuerier 查询 Agent 可用性正常
- [ ] IToolQuerier 查询工具列表正常
- [ ] EventBus 事件订阅 (insights/audit) 不影响主流程
- [ ] SSE EventSourceResponse 流式响应格式不变

#### 数据库
- [ ] Conversation/Message ORM 模型正常
- [ ] TeamExecution ORM 模型正常
- [ ] 流式响应后独立 DB session 持久化正常

#### 认证
- [ ] 未认证请求返回 401
- [ ] 非 owner 操作返回 403/404

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# 域实体测试
pytest backend/tests/modules/execution/unit/domain/ -v

# 应用服务测试
pytest backend/tests/modules/execution/unit/application/ -v

# 基础设施适配器测试
pytest backend/tests/modules/execution/unit/infrastructure/ -v

# 集成测试
pytest backend/tests/modules/execution/integration/ -v

# 全量
pytest backend/tests/modules/execution/ -v --tb=short
```
