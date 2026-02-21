## EVAL: agentcore-integration
Created: 2026-02-21

### Capability Evals

#### ClaudeAgentAdapter (核心执行适配器)
- [ ] 正确调用 claude_agent_sdk.query() 执行 Agent 对话
- [ ] system_prompt + 历史消息正确组装为 SDK 输入
- [ ] max_turns 配置正确传递 (默认 25, Teams 模式 200)
- [ ] temperature/model_id/max_tokens 配置正确传递
- [ ] 流式响应 (yield chunks) 正常工作
- [ ] Teams 模式注入 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 环境变量
- [ ] MCP Server 工具通过 IToolQuerier 动态加载
- [ ] SDK 异常 (claude_agent_sdk 错误) 正确捕获并转换为 DomainError
- [ ] SSRF 防护: 阻止访问内部/私有 IP 地址

#### AgentCoreRuntimeAdapter (Runtime 执行路径)
- [ ] 正确调用 bedrock invoke_inline_agent API
- [ ] 执行路由: providers.py 依赖注入 + ExecutionService._should_use_agent_runtime 条件路由 (runtime_type=="agent" 且有 agent_runtime 时路由到 ClaudeAgentAdapter)
- [ ] 无 agent_runtime 时自动降级到 ILLMClient (Bedrock Converse API 降级路径)
- [ ] AgentCore Runtime 健康状态由 AWS 托管 (非应用层探针)

#### Identity 集成 (C-P3-3)
- [ ] OAuth 2.0 Provider 配置正确
- [ ] Gateway 入站认证令牌验证
- [ ] Token 交换流程 (平台 JWT ↔ AgentCore Identity Token)
- [ ] Token Vault 第三方 API Key 存储/检索
- [ ] Token Vault 加密存储安全

#### Memory 集成 (C-P3-1)
- [ ] MemoryAdapter 正确调用 AgentCore Memory API
- [ ] 记忆策略配置 (session/long-term/working)
- [ ] ConversationCompleted 事件触发记忆提取
- [ ] Agent 执行时自动注入长期记忆上下文
- [ ] MemoryMCPServer 作为 MCP Server 提供记忆能力
- [ ] 记忆提取异步执行不阻塞主流程

#### A2A 通信 (C-P3-2)
- [ ] A2AAdapter 实现跨 Runtime Agent 通信
- [ ] Agent-to-Agent 消息格式正确
- [ ] A2A 超时控制和错误处理
- [ ] A2A 有限采纳策略 (ADR-011): 仅内部平台 Agent 间通信

#### Gateway 工具同步 (C-P2-1)
- [ ] ToolApproved 事件触发 Gateway 工具注册
- [ ] ToolDeprecated 事件触发 Gateway 工具注销
- [ ] GatewaySyncAdapter 正确调用 AgentCore Gateway API
- [ ] gateway_target_id 正确存储到 Tool 实体
- [ ] 同步失败不阻塞工具审批主流程

#### SDK 消息工具
- [ ] sdk_message_utils 正确转换 Message → SDK 格式
- [ ] 历史消息滑动窗口在 ExecutionService._truncate_messages 中实现 (非 sdk_message_utils)
- [ ] system_prompt 作为独立参数传递 (非消息列表)

#### Agent 入口点 (agent_entrypoint.py)
- [ ] agent_entrypoint.py 使用 claude_agent_sdk.query() 直接调用 (非 BedrockAgentCoreApp 类)
- [ ] Claude Agent SDK 集成正确
- [ ] 工具注册/知识库集成正常
- [ ] Dockerfile.agent 构建成功 (镜像 < 800MB)

### Regression Evals

#### SDK 兼容性
- [ ] claude-agent-sdk 0.1.35 API 不变
- [ ] bedrock-agentcore 1.3.0 API 不变
- [ ] boto3 Bedrock API 兼容性正常

#### 配置切换
- [ ] AGENT_RUNTIME_MODE 默认 "local" 不影响现有部署
- [ ] 新增配置项有合理默认值

#### 跨模块依赖
- [ ] IAgentRuntime 接口不变 (ExecutionService 依赖)
- [ ] IMemoryService 接口不变
- [ ] 事件订阅不影响主业务流程

#### 安全
- [ ] Identity Token 正确过期和刷新
- [ ] Token Vault 加密密钥管理正确
- [ ] A2A 通信仅限内部 Agent

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# ClaudeAgentAdapter 测试
pytest backend/tests/modules/execution/unit/infrastructure/test_claude_agent_adapter.py -v

# AgentCoreRuntimeAdapter 测试
pytest backend/tests/modules/execution/unit/infrastructure/test_agentcore_runtime_adapter.py -v

# Memory 集成测试
pytest backend/tests/modules/execution/unit/infrastructure/test_memory*.py -v

# A2A 适配器测试
pytest backend/tests/modules/execution/unit/infrastructure/test_a2a_adapter.py -v

# Identity 适配器测试
pytest backend/tests/modules/execution/unit/infrastructure/test_identity_adapter.py -v

# Token Vault 测试
pytest backend/tests/modules/execution/unit/infrastructure/test_token_vault_adapter.py -v

# Gateway 同步测试
pytest backend/tests/modules/tool_catalog/unit/infrastructure/test_gateway*.py -v

# SDK 消息工具测试
pytest backend/tests/modules/execution/unit/infrastructure/test_sdk_message_utils.py -v

# Agent 入口点测试
pytest backend/tests/test_agent_entrypoint.py -v

# 全量基础设施适配器
pytest backend/tests/modules/execution/unit/infrastructure/ -v --tb=short
```
