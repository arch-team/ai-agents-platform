/**
 * E2E 测试 mock 数据常量
 * 集中管理所有 Playwright E2E 测试所需的 mock 数据
 */

// 认证相关
export const AUTH_TOKEN = {
  access_token: 'test-token',
  token_type: 'bearer',
};

export const CURRENT_USER = {
  id: 1,
  username: 'testuser',
  name: '测试用户',
  email: 'test@example.com',
  role: 'admin' as const,
};

export const LOGIN_CREDENTIALS = {
  email: 'test@example.com',
  password: 'Password1',
};

// Agent 相关
export const MOCK_AGENTS = [
  {
    id: 1,
    name: '客服助手',
    description: '处理客户常见问题的 AI 助手',
    system_prompt: '你是一个客服助手',
    status: 'draft' as const,
    owner_id: 1,
    config: { model_id: 'claude-3-5-sonnet', temperature: 0.7, max_tokens: 4096, top_p: 1 },
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: '代码审查助手',
    description: '自动审查代码质量的 AI 助手',
    system_prompt: '你是一个代码审查助手',
    status: 'active' as const,
    owner_id: 1,
    config: { model_id: 'claude-3-5-sonnet', temperature: 0.3, max_tokens: 8192, top_p: 1 },
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
  {
    id: 3,
    name: '文档生成器',
    description: '已归档的文档生成助手',
    system_prompt: '你是一个文档生成助手',
    status: 'archived' as const,
    owner_id: 1,
    config: { model_id: 'claude-3', temperature: 0.5, max_tokens: 4096, top_p: 1 },
    created_at: '2024-12-01T00:00:00Z',
    updated_at: '2025-01-03T00:00:00Z',
  },
];

// Dashboard 相关
export const DASHBOARD_SUMMARY = {
  total_agents: 15,
  active_agents: 8,
  total_invocations: 12500,
  total_tokens: 2500000,
  total_cost: 125.5,
  period: { start_date: '2025-01-01', end_date: '2025-01-31' },
};

export const DASHBOARD_STATS = {
  agents_total: 3,
  conversations_total: 10,
  team_executions_total: 5,
};

// 对话相关
export const MOCK_CONVERSATIONS = [
  {
    id: 1,
    title: '测试对话',
    agent_id: 1,
    user_id: 1,
    status: 'active',
    message_count: 3,
    total_tokens: 100,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
];

// 团队执行相关
export const MOCK_TEAM_EXECUTIONS = [
  {
    id: 1,
    agent_id: 1,
    user_id: 1,
    prompt: '测试执行',
    status: 'completed',
    result: '执行完成',
    error: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
];

// 知识库相关 (状态必须大写: CREATING | ACTIVE | SYNCING | FAILED)
export const MOCK_KNOWLEDGE_BASES = [
  {
    id: 1,
    name: '产品文档库',
    description: '包含所有产品相关文档',
    status: 'ACTIVE',
    document_count: 15,
    owner_id: 1,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'FAQ 知识库',
    description: '常见问题解答',
    status: 'CREATING',
    document_count: 0,
    owner_id: 1,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

// 模板相关 (状态小写: draft | published | archived)
export const MOCK_TEMPLATES = [
  {
    id: 1,
    name: '客服模板',
    description: '适用于客服场景的 Agent 模板',
    category: 'customer_service',
    status: 'published',
    usage_count: 42,
    owner_id: 1,
    config: { model_id: 'claude-3-5-sonnet', temperature: 0.7, max_tokens: 4096 },
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: '代码助手模板',
    description: '适用于代码开发场景',
    category: 'development',
    status: 'draft',
    usage_count: 0,
    owner_id: 1,
    config: { model_id: 'claude-3-5-sonnet', temperature: 0.3, max_tokens: 8192 },
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

// 工具相关 (状态必须大写: DRAFT | PENDING_REVIEW | APPROVED | REJECTED | DEPRECATED)
// (类型必须大写: MCP_SERVER | API | FUNCTION)
export const MOCK_TOOLS = [
  {
    id: '1',
    name: '天气查询',
    description: '查询指定城市的天气信息',
    tool_type: 'API',
    status: 'APPROVED',
    version: '1.0.0',
    configuration: {},
    created_by: 'testuser',
    owner_id: 1,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: '代码执行器',
    description: '安全执行 Python 代码片段',
    tool_type: 'MCP_SERVER',
    status: 'PENDING_REVIEW',
    version: '0.1.0',
    configuration: {},
    created_by: 'testuser',
    owner_id: 1,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

// 评估测试集相关 (状态小写: draft | active | archived)
export const MOCK_TEST_SUITES = [
  {
    id: 1,
    name: '客服质量测试集',
    description: '评估客服 Agent 的回答质量',
    status: 'active',
    owner_id: 1,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: '代码审查测试集',
    description: '评估代码审查 Agent 的准确性',
    status: 'draft',
    owner_id: 1,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

// 分页响应辅助函数
export function paginatedResponse<T>(items: T[], page = 1, pageSize = 10) {
  return {
    items,
    total: items.length,
    page,
    page_size: pageSize,
    total_pages: Math.ceil(items.length / pageSize),
  };
}
