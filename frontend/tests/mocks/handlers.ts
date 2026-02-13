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

  http.get(`${BASE_URL}/api/v1/agents/:id`, () =>
    HttpResponse.json(mockAgent),
  ),

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
      return HttpResponse.json(
        { code: 'EMAIL_EXISTS', message: '邮箱已被注册' },
        { status: 409 },
      );
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
    return HttpResponse.json(
      { ...mockConversation, ...body, id: 2 },
      { status: 201 },
    );
  }),

  // Team Executions
  http.get(`${BASE_URL}/api/v1/team-executions`, () =>
    HttpResponse.json({
      items: [
        {
          id: 1,
          name: '测试 Team 执行',
          goal: '完成测试任务',
          status: 'completed',
          agent_ids: [1],
          created_by: 1,
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
];
