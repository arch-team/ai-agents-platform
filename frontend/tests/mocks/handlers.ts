import { http, HttpResponse } from 'msw';

const BASE_URL = 'http://localhost:8000';

const mockAgent = {
  id: 1,
  name: '测试 Agent',
  description: '一个测试用的 Agent',
  system_prompt: '你是一个助手',
  status: 'active',
  owner_id: 1,
  config: { model_id: 'claude-3', temperature: 0.7, max_tokens: 4096, top_p: 1 },
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

const mockConversation = {
  id: 1,
  title: '测试对话',
  agent_id: 1,
  user_id: 1,
  status: 'active',
  message_count: 3,
  total_tokens: 100,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

export const handlers = [
  // Agents
  http.get(`${BASE_URL}/api/v1/agents`, () =>
    HttpResponse.json({
      items: [mockAgent],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/agents/:id`, () => HttpResponse.json(mockAgent)),

  http.post(`${BASE_URL}/api/v1/agents`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: 1,
        ...body,
        status: 'draft',
        owner_id: 1,
        config: { model_id: 'claude-3-5-sonnet', temperature: 0.7, max_tokens: 4096, top_p: 1 },
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
      { status: 201 },
    );
  }),

  http.post(`${BASE_URL}/api/v1/agents/:id/activate`, () =>
    HttpResponse.json({ ...mockAgent, status: 'active' }),
  ),

  http.post(`${BASE_URL}/api/v1/agents/:id/archive`, () =>
    HttpResponse.json({ ...mockAgent, status: 'archived' }),
  ),

  // Auth
  http.post(`${BASE_URL}/api/v1/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };
    if (body.email === 'test@example.com' && body.password === 'Password1') {
      return HttpResponse.json({
        access_token: 'fake-jwt-token',
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com', name: '测试用户', role: 'admin' },
      });
    }
    return HttpResponse.json(
      { code: 'INVALID_CREDENTIALS', message: '账号或密码错误' },
      { status: 401 },
    );
  }),

  http.post(`${BASE_URL}/api/v1/auth/register`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string; name: string };
    if (body.email === 'existing@example.com') {
      return HttpResponse.json({ code: 'EMAIL_EXISTS', message: '邮箱已被注册' }, { status: 409 });
    }
    return HttpResponse.json({ message: '注册成功' }, { status: 201 });
  }),

  http.get(`${BASE_URL}/api/v1/auth/me`, () =>
    HttpResponse.json({
      id: 1,
      email: 'test@example.com',
      name: '测试用户',
      role: 'admin',
    }),
  ),

  // Conversations
  http.get(`${BASE_URL}/api/v1/conversations`, () =>
    HttpResponse.json({
      items: [mockConversation],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/conversations/:id`, () =>
    HttpResponse.json({
      conversation: mockConversation,
      messages: [
        {
          id: 1,
          conversation_id: 1,
          role: 'user',
          content: '你好',
          token_count: 5,
          created_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 2,
          conversation_id: 1,
          role: 'assistant',
          content: '你好！有什么可以帮助你的吗？',
          token_count: 20,
          created_at: '2025-01-01T00:01:00Z',
        },
      ],
    }),
  ),

  http.post(`${BASE_URL}/api/v1/conversations`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockConversation, ...body, id: 2 }, { status: 201 });
  }),

  // Dashboard Stats
  http.get(`${BASE_URL}/api/v1/stats/summary`, () =>
    HttpResponse.json({
      agents_total: 1,
      conversations_total: 1,
      team_executions_total: 1,
    }),
  ),

  // Knowledge Bases
  http.get(`${BASE_URL}/api/v1/knowledge-bases`, () =>
    HttpResponse.json({
      items: [
        {
          id: 1,
          name: '测试知识库',
          description: '测试用知识库',
          status: 'ACTIVE',
          document_count: 5,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/knowledge-bases/:id`, () =>
    HttpResponse.json({
      id: 1,
      name: '测试知识库',
      description: '测试用知识库',
      status: 'ACTIVE',
      document_count: 5,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  http.get(`${BASE_URL}/api/v1/knowledge-bases/:id/documents`, () =>
    HttpResponse.json({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    }),
  ),

  http.post(`${BASE_URL}/api/v1/knowledge-bases`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: 2,
        ...body,
        status: 'CREATING',
        document_count: 0,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
      { status: 201 },
    );
  }),

  http.delete(
    `${BASE_URL}/api/v1/knowledge-bases/:id`,
    () => new HttpResponse(null, { status: 204 }),
  ),

  http.post(`${BASE_URL}/api/v1/knowledge-bases/:id/sync`, ({ params }) =>
    HttpResponse.json({
      id: Number(params.id),
      name: '测试知识库',
      description: '测试用知识库',
      status: 'SYNCING',
      document_count: 5,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  // Templates
  http.get(`${BASE_URL}/api/v1/templates`, () =>
    HttpResponse.json({
      items: [
        {
          id: 1,
          name: '测试模板',
          description: '测试用模板',
          category: 'customer_service',
          status: 'published',
          system_prompt: '你是助手',
          config: { model_id: 'claude-3-5-sonnet', temperature: 0.7, max_tokens: 4096 },
          author: '管理员',
          use_count: 10,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 12,
      total_pages: 1,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/templates/published`, () =>
    HttpResponse.json({
      items: [],
      total: 0,
      page: 1,
      page_size: 12,
      total_pages: 0,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/templates/:id`, () =>
    HttpResponse.json({
      id: 1,
      name: '测试模板',
      description: '测试用模板',
      category: 'customer_service',
      status: 'published',
      system_prompt: '你是助手',
      config: { model_id: 'claude-3-5-sonnet', temperature: 0.7, max_tokens: 4096 },
      author: '管理员',
      use_count: 10,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  http.post(`${BASE_URL}/api/v1/templates`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: 2,
        ...body,
        status: 'draft',
        author: '管理员',
        use_count: 0,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
      { status: 201 },
    );
  }),

  http.delete(`${BASE_URL}/api/v1/templates/:id`, () => new HttpResponse(null, { status: 204 })),

  http.post(`${BASE_URL}/api/v1/templates/:id/publish`, ({ params }) =>
    HttpResponse.json({
      id: Number(params.id),
      name: '测试模板',
      status: 'published',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  http.post(`${BASE_URL}/api/v1/templates/:id/archive`, ({ params }) =>
    HttpResponse.json({
      id: Number(params.id),
      name: '测试模板',
      status: 'archived',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  // Tools
  http.get(`${BASE_URL}/api/v1/tools`, () =>
    HttpResponse.json({
      items: [
        {
          id: 'tool-1',
          name: '测试工具',
          description: '测试用工具',
          tool_type: 'MCP_SERVER',
          status: 'APPROVED',
          version: '1.0.0',
          configuration: {},
          created_by: 'admin',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/tools/approved`, () =>
    HttpResponse.json({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/tools/:id`, () =>
    HttpResponse.json({
      id: 'tool-1',
      name: '测试工具',
      description: '测试用工具',
      tool_type: 'MCP_SERVER',
      status: 'APPROVED',
      version: '1.0.0',
      configuration: {},
      created_by: 'admin',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  http.post(`${BASE_URL}/api/v1/tools`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: 'tool-2',
        ...body,
        status: 'DRAFT',
        configuration: {},
        created_by: 'admin',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
      { status: 201 },
    );
  }),

  http.delete(`${BASE_URL}/api/v1/tools/:id`, () => new HttpResponse(null, { status: 204 })),

  // Team Executions
  http.get(`${BASE_URL}/api/v1/team-executions`, () =>
    HttpResponse.json({
      items: [
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
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/team-executions/:id`, () =>
    HttpResponse.json({
      id: 1,
      agent_id: 1,
      user_id: 1,
      prompt: '测试执行',
      status: 'completed',
      result: '执行完成',
      error: null,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  http.get(`${BASE_URL}/api/v1/team-executions/:id/logs`, () => HttpResponse.json([])),

  http.post(`${BASE_URL}/api/v1/team-executions`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: 2,
        ...body,
        user_id: 1,
        status: 'pending',
        result: null,
        error: null,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
      { status: 201 },
    );
  }),

  http.post(`${BASE_URL}/api/v1/team-executions/:id/cancel`, ({ params }) =>
    HttpResponse.json({
      id: Number(params.id),
      agent_id: 1,
      user_id: 1,
      prompt: '测试执行',
      status: 'cancelled',
      result: null,
      error: null,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  // Test Suites
  http.get(`${BASE_URL}/api/v1/test-suites`, () =>
    HttpResponse.json({
      items: [
        {
          id: 1,
          name: '回归测试集',
          description: '核心功能回归测试',
          agent_id: 1,
          status: 'draft',
          owner_id: 1,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 2,
          name: '性能测试集',
          description: '性能基准测试',
          agent_id: 1,
          status: 'active',
          owner_id: 1,
          created_at: '2025-01-02T00:00:00Z',
          updated_at: '2025-01-02T00:00:00Z',
        },
      ],
      total: 2,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/test-suites/:id`, ({ params }) =>
    HttpResponse.json({
      id: Number(params.id),
      name: '回归测试集',
      description: '核心功能回归测试',
      agent_id: 1,
      status: 'draft',
      owner_id: 1,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  http.post(`${BASE_URL}/api/v1/test-suites`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: 3,
        ...body,
        status: 'draft',
        owner_id: 1,
        created_at: '2025-01-03T00:00:00Z',
        updated_at: '2025-01-03T00:00:00Z',
      },
      { status: 201 },
    );
  }),

  http.post(`${BASE_URL}/api/v1/test-suites/:id/activate`, ({ params }) =>
    HttpResponse.json({
      id: Number(params.id),
      name: '回归测试集',
      description: '核心功能回归测试',
      agent_id: 1,
      status: 'active',
      owner_id: 1,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }),
  ),

  http.post(`${BASE_URL}/api/v1/test-suites/:id/archive`, ({ params }) =>
    HttpResponse.json({
      id: Number(params.id),
      name: '性能测试集',
      description: '性能基准测试',
      agent_id: 1,
      status: 'archived',
      owner_id: 1,
      created_at: '2025-01-02T00:00:00Z',
      updated_at: '2025-01-02T00:00:00Z',
    }),
  ),

  http.delete(`${BASE_URL}/api/v1/test-suites/:id`, () => new HttpResponse(null, { status: 204 })),

  // Test Cases
  http.get(`${BASE_URL}/api/v1/test-suites/:suiteId/cases`, () =>
    HttpResponse.json({
      items: [
        {
          id: 1,
          suite_id: 1,
          input_prompt: '你好，请自我介绍',
          expected_output: '我是 AI 助手',
          evaluation_criteria: '包含自我介绍',
          order_index: 0,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),
  ),

  http.post(`${BASE_URL}/api/v1/test-suites/:suiteId/cases`, async ({ request, params }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: 2,
        suite_id: Number(params.suiteId),
        ...body,
        order_index: 1,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
      { status: 201 },
    );
  }),

  // Evaluation Runs
  http.get(`${BASE_URL}/api/v1/evaluation-runs`, () =>
    HttpResponse.json({
      items: [
        {
          id: 1,
          suite_id: 1,
          agent_id: 1,
          user_id: 1,
          status: 'completed',
          total_cases: 10,
          passed_cases: 8,
          failed_cases: 2,
          score: 0.85,
          started_at: '2025-01-01T00:00:00Z',
          completed_at: '2025-01-01T00:05:00Z',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:05:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),
  ),

  http.get(`${BASE_URL}/api/v1/evaluation-runs/:id`, ({ params }) =>
    HttpResponse.json({
      id: Number(params.id),
      suite_id: 1,
      agent_id: 1,
      user_id: 1,
      status: 'completed',
      total_cases: 10,
      passed_cases: 8,
      failed_cases: 2,
      score: 0.85,
      started_at: '2025-01-01T00:00:00Z',
      completed_at: '2025-01-01T00:05:00Z',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:05:00Z',
    }),
  ),

  http.post(`${BASE_URL}/api/v1/evaluation-runs`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: 2,
        suite_id: body.suite_id,
        agent_id: 1,
        user_id: 1,
        status: 'pending',
        total_cases: 0,
        passed_cases: 0,
        failed_cases: 0,
        score: 0,
        started_at: null,
        completed_at: null,
        created_at: '2025-01-02T00:00:00Z',
        updated_at: '2025-01-02T00:00:00Z',
      },
      { status: 201 },
    );
  }),

  http.get(`${BASE_URL}/api/v1/evaluation-runs/:runId/results`, () =>
    HttpResponse.json({
      items: [
        {
          id: 1,
          run_id: 1,
          case_id: 1,
          actual_output: '我是 AI 助手，很高兴为您服务',
          score: 0.9,
          passed: true,
          error_message: '',
          created_at: '2025-01-01T00:01:00Z',
          updated_at: '2025-01-01T00:01:00Z',
        },
        {
          id: 2,
          run_id: 1,
          case_id: 2,
          actual_output: '',
          score: 0.2,
          passed: false,
          error_message: '超时未响应',
          created_at: '2025-01-01T00:02:00Z',
          updated_at: '2025-01-01T00:02:00Z',
        },
      ],
      total: 2,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),
  ),

  // Eval Pipelines
  http.get(`${BASE_URL}/api/v1/eval-suites/:suiteId/pipelines`, () =>
    HttpResponse.json([
      {
        id: 1,
        suite_id: 1,
        agent_id: 1,
        trigger: 'manual',
        model_ids: ['us.anthropic.claude-haiku-4-20250514-v1:0'],
        status: 'completed',
        bedrock_job_id: 'job-123',
        score_summary: { accuracy: 0.85, relevance: 0.92 },
        error_message: null,
        started_at: '2026-02-21T10:00:00Z',
        completed_at: '2026-02-21T10:15:00Z',
        created_at: '2026-02-21T10:00:00Z',
      },
    ]),
  ),

  http.post(`${BASE_URL}/api/v1/eval-suites/:suiteId/pipelines`, () =>
    HttpResponse.json(
      {
        id: 2,
        suite_id: 1,
        agent_id: 1,
        trigger: 'manual',
        model_ids: [],
        status: 'scheduled',
        bedrock_job_id: null,
        score_summary: {},
        error_message: null,
        started_at: null,
        completed_at: null,
        created_at: '2026-02-21T12:00:00Z',
      },
      { status: 201 },
    ),
  ),

  // Insights
  http.get(`${BASE_URL}/api/v1/insights/summary`, () =>
    HttpResponse.json({
      total_agents: 15,
      active_agents: 8,
      total_invocations: 12500,
      total_tokens: 2500000,
      total_cost: 125.5,
      period: { start_date: '2025-01-01', end_date: '2025-01-31' },
    }),
  ),

  http.get(`${BASE_URL}/api/v1/insights/cost-breakdown`, () =>
    HttpResponse.json({
      items: [
        {
          agent_id: '1',
          agent_name: '客服助手',
          total_tokens: 500000,
          tokens_input: 300000,
          tokens_output: 200000,
          invocation_count: 2500,
        },
        {
          agent_id: '2',
          agent_name: '代码审查助手',
          total_tokens: 300000,
          tokens_input: 180000,
          tokens_output: 120000,
          invocation_count: 1200,
        },
      ],
      total_tokens: 800000,
      period: { start_date: '2025-01-01', end_date: '2025-01-31' },
    }),
  ),

  http.get(`${BASE_URL}/api/v1/insights/usage-trends`, () =>
    HttpResponse.json({
      data_points: [
        { date: '2025-01-01', invocation_count: 100, total_tokens: 50000, unique_users: 10 },
        { date: '2025-01-02', invocation_count: 150, total_tokens: 75000, unique_users: 12 },
        { date: '2025-01-03', invocation_count: 120, total_tokens: 60000, unique_users: 11 },
      ],
      period: { start_date: '2025-01-01', end_date: '2025-01-03' },
    }),
  ),
];
