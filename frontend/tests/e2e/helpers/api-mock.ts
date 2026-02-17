import type { Page } from '@playwright/test';
import {
  AUTH_TOKEN,
  CURRENT_USER,
  MOCK_AGENTS,
  DASHBOARD_SUMMARY,
  DASHBOARD_STATS,
  MOCK_CONVERSATIONS,
  MOCK_TEAM_EXECUTIONS,
  MOCK_KNOWLEDGE_BASES,
  MOCK_TEMPLATES,
  MOCK_TOOLS,
  MOCK_TEST_SUITES,
  paginatedResponse,
} from '../fixtures/mock-data';

const API_BASE = '**/api/v1';

/**
 * Mock 认证相关 API
 * - POST /api/v1/auth/login → 返回 token
 * - GET /api/v1/auth/me → 返回当前用户信息
 */
export async function mockAuth(page: Page) {
  await page.route(`${API_BASE}/auth/login`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ...AUTH_TOKEN,
        user: CURRENT_USER,
      }),
    });
  });

  await page.route(`${API_BASE}/auth/me`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(CURRENT_USER),
    });
  });
}

/**
 * Mock Agent 相关 API
 * - GET /api/v1/agents → 返回 Agent 列表
 * - GET /api/v1/agents/:id → 返回单个 Agent 详情
 */
export async function mockAgents(page: Page) {
  // 使用正则匹配 /api/v1/agents 及带查询参数的 URL（如 ?page=1&page_size=10）
  // 但不匹配 /api/v1/agents/1 等子路径
  await page.route(/\/api\/v1\/agents(\?.*)?$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(paginatedResponse(MOCK_AGENTS)),
      });
    } else if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 4,
          ...body,
          status: 'draft',
          owner_id: 1,
          config: { model_id: 'claude-3-5-sonnet', temperature: 0.7, max_tokens: 4096, top_p: 1 },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    }
  });

  // Agent 详情 (匹配 /agents/数字 的路径)
  await page.route(/\/api\/v1\/agents\/\d+$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_AGENTS[0]),
      });
    }
  });
}

/**
 * Mock Dashboard 相关 API
 * - GET /api/v1/insights/summary → 返回 insights 摘要
 * - GET /api/v1/stats/summary → 返回统计摘要
 */
export async function mockDashboard(page: Page) {
  await page.route(/\/api\/v1\/insights\/summary(\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(DASHBOARD_SUMMARY),
    });
  });

  await page.route(/\/api\/v1\/stats\/summary(\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(DASHBOARD_STATS),
    });
  });

  await page.route(/\/api\/v1\/insights\/cost-breakdown(\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            agent_id: '1',
            agent_name: '客服助手',
            total_tokens: 500000,
            tokens_input: 300000,
            tokens_output: 200000,
            invocation_count: 2500,
          },
        ],
        total_tokens: 500000,
        period: { start_date: '2025-01-01', end_date: '2025-01-31' },
      }),
    });
  });

  await page.route(/\/api\/v1\/insights\/usage-trends(\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data_points: [
          { date: '2025-01-01', invocation_count: 100, total_tokens: 50000, unique_users: 10 },
          { date: '2025-01-02', invocation_count: 150, total_tokens: 75000, unique_users: 12 },
        ],
        period: { start_date: '2025-01-01', end_date: '2025-01-02' },
      }),
    });
  });
}

/**
 * Mock 对话相关 API
 */
export async function mockConversations(page: Page) {
  await page.route(/\/api\/v1\/conversations(\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(paginatedResponse(MOCK_CONVERSATIONS)),
    });
  });
}

/**
 * Mock 团队执行相关 API
 */
export async function mockTeamExecutions(page: Page) {
  await page.route(/\/api\/v1\/team-executions(\?.*)?$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(paginatedResponse(MOCK_TEAM_EXECUTIONS, 1, 20)),
      });
    }
  });
}

/**
 * Mock 知识库相关 API
 */
export async function mockKnowledgeBases(page: Page) {
  await page.route(/\/api\/v1\/knowledge-bases(\?.*)?$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(paginatedResponse(MOCK_KNOWLEDGE_BASES)),
      });
    } else if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 3,
          ...body,
          status: 'CREATING',
          document_count: 0,
          owner_id: 1,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    }
  });

  await page.route(/\/api\/v1\/knowledge-bases\/\d+$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_KNOWLEDGE_BASES[0]),
      });
    }
  });
}

/**
 * Mock 模板相关 API
 */
export async function mockTemplates(page: Page) {
  await page.route(/\/api\/v1\/templates(\?.*)?$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(paginatedResponse(MOCK_TEMPLATES)),
      });
    }
  });
}

/**
 * Mock 工具相关 API
 */
export async function mockTools(page: Page) {
  await page.route(/\/api\/v1\/tools(\?.*)?$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(paginatedResponse(MOCK_TOOLS)),
      });
    }
  });
}

/**
 * Mock 评估相关 API
 */
export async function mockEvaluation(page: Page) {
  await page.route(/\/api\/v1\/test-suites(\?.*)?$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(paginatedResponse(MOCK_TEST_SUITES)),
      });
    }
  });

  // 评估运行列表
  await page.route(/\/api\/v1\/evaluation-runs(\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(paginatedResponse([])),
    });
  });
}

/**
 * Mock 所有 API — 在测试中一次性 mock 全部接口
 */
export async function mockAll(page: Page) {
  await mockAuth(page);
  await mockAgents(page);
  await mockDashboard(page);
  await mockConversations(page);
  await mockTeamExecutions(page);
  await mockKnowledgeBases(page);
  await mockTemplates(page);
  await mockTools(page);
  await mockEvaluation(page);
}
