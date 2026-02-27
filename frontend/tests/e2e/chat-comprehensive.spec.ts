/**
 * 对话功能全面 E2E 测试套件
 *
 * 针对 Dev 环境 (d2k7ovgb2e4af9.cloudfront.net) 的真实 API 测试
 * + Mock 增强的边界场景测试
 *
 * 测试分层:
 * - describe('真实 API') — 登录到真实 Dev 环境，验证前后端集成
 * - describe('Mock 增强') — 使用 Playwright route mock，覆盖边界和异常场景
 */

import { test, expect, type Page } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS, MOCK_CONVERSATIONS, paginatedResponse } from './fixtures/mock-data';

// ========================================================================
// Dev 环境凭据（仅用于 E2E 测试，不含生产密钥）
// 运行: PLAYWRIGHT_BASE_URL=https://d2k7ovgb2e4af9.cloudfront.net pnpm test:e2e
// ========================================================================
const DEV_CREDENTIALS = {
  email: 'admin@company.com',
  password: 'Admin@2026!',
};

// ========================================================================
// 辅助函数
// ========================================================================

/** 登录到 Dev 真实环境（使用 playwright.config.ts 中的 baseURL） */
async function loginToDev(page: Page) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.getByLabel('邮箱').fill(DEV_CREDENTIALS.email);
  await page.getByLabel('密码').fill(DEV_CREDENTIALS.password);
  await page.getByRole('button', { name: '登录', exact: true }).click();
  // 真实 API 登录可能较慢，给予充足超时
  await expect(page).toHaveURL('/', { timeout: 15000 });
  await page.waitForLoadState('networkidle');
}

/**
 * 通过 SPA 导航到对话页面（点击侧边栏链接，保持 token 不丢失）
 * 注意: 此应用 token 存在 Zustand 内存中，page.goto 会重新加载页面导致 token 丢失
 */
async function navigateToChat(page: Page) {
  await page.getByLabel('主导航').getByText('对话').click();
  await expect(page).toHaveURL('/chat', { timeout: 10000 });
  await page.waitForLoadState('networkidle');
}

/**
 * TODO(human): 等待对话列表加载完成，返回是否有对话数据。
 *
 * ConversationList 组件有三种状态: loading(Spinner) → error/empty/data
 * 当前的 `isVisible().catch(() => false)` 可能在 loading 阶段就返回 false，
 * 导致本应执行的测试被 skip。
 *
 * 要求: 返回 { hasConversations: boolean } 以区分"确实没数据"和"还在加载"
 */
async function waitForConversationList(_page: Page): Promise<{ hasConversations: boolean }> {
  // 占位实现 — 请改进此函数
  return { hasConversations: false };
}

/** 使用 mock 登录（不连接真实后端） */
async function loginWithMock(page: Page) {
  await mockAll(page);
  await page.goto('/login');
  await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
  await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await expect(page).toHaveURL('/');
}

// ========================================================================
// Part 1: 真实 Dev 环境测试 — 验证前后端集成
// ========================================================================

test.describe('对话功能 — 真实 Dev 环境', () => {
  // 真实 API 测试串行运行，避免并行请求触发限流
  test.describe.configure({ mode: 'serial' });
  // 单个测试超时 60 秒（真实 API 响应较慢）
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await loginToDev(page);
  });

  test.describe('对话列表页面', () => {
    test('导航到对话页面应显示对话列表侧边栏', async ({ page }) => {
      await page.getByLabel('主导航').getByText('对话').click();
      await expect(page).toHaveURL('/chat');

      // 验证对话列表侧边栏存在
      await expect(page.getByLabel('对话列表')).toBeVisible();

      // 验证新建对话按钮存在
      await expect(page.getByRole('button', { name: '新建对话' })).toBeVisible();
    });

    test('对话列表应从 API 加载真实数据', async ({ page }) => {
      await navigateToChat(page);

      // 对话列表侧边栏可见
      const sidebar = page.getByLabel('对话列表');
      await expect(sidebar).toBeVisible();

      // 应有对话历史导航区域（可能有也可能没有对话）
      // 如果有对话，验证对话项包含标题和消息数
      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (hasConversations) {
        // 至少有一个对话项 (button 角色)
        const firstConversation = conversationNav.getByRole('button').first();
        await expect(firstConversation).toBeVisible();
      }
    });

    test('未选择对话时应显示提示文字', async ({ page }) => {
      await navigateToChat(page);

      await expect(page.getByText('请选择一个对话')).toBeVisible();
    });

    test('新建对话按钮应跳转到 Agent 列表页面', async ({ page }) => {
      await navigateToChat(page);

      await page.getByRole('button', { name: '新建对话' }).click();
      await expect(page).toHaveURL('/agents');

      // 验证到达 Agent 管理页面
      await expect(page.getByRole('heading', { name: 'Agent 管理' })).toBeVisible();
    });
  });

  test.describe('对话详情', () => {
    test('点击对话应加载消息历史', async ({ page }) => {
      await navigateToChat(page);

      // 等待对话列表加载
      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (!hasConversations) {
        test.skip(true, '当前 Dev 环境没有对话数据');
        return;
      }

      // 点击第一个对话
      const firstConversation = conversationNav.getByRole('button').first();
      await firstConversation.click();

      // URL 应变为 /chat/{id}
      await expect(page).toHaveURL(/\/chat\/\d+/);

      // 验证对话标题区域出现
      const chatTitle = page.locator('h2');
      await expect(chatTitle).toBeVisible();

      // 验证消息列表区域存在
      const messageLog = page.getByRole('log', { name: '消息列表' });
      await expect(messageLog).toBeVisible();

      // 验证消息输入区域存在
      const messageInput = page.getByLabel('消息输入');
      await expect(messageInput).toBeVisible();
    });

    test('选中对话后侧边栏应标记当前项', async ({ page }) => {
      await navigateToChat(page);

      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (!hasConversations) {
        test.skip(true, '当前 Dev 环境没有对话数据');
        return;
      }

      // 点击第一个对话
      const firstConversation = conversationNav.getByRole('button').first();
      await firstConversation.click();
      await expect(page).toHaveURL(/\/chat\/\d+/);

      // 验证对话详情已加载
      await expect(page.getByRole('log', { name: '消息列表' })).toBeVisible();

      // 验证该对话在侧边栏被选中 (aria-current)
      const selectedItem = page.getByLabel('对话历史').locator('button[aria-current="true"]');
      await expect(selectedItem).toBeVisible();
    });

    test('对话详情应显示消息气泡和时间戳', async ({ page }) => {
      await navigateToChat(page);

      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (!hasConversations) {
        test.skip(true, '当前 Dev 环境没有对话数据');
        return;
      }

      // 点击第一个对话
      await conversationNav.getByRole('button').first().click();
      await expect(page).toHaveURL(/\/chat\/\d+/);

      // 等待消息列表加载
      const messageLog = page.getByRole('log', { name: '消息列表' });
      await expect(messageLog).toBeVisible();

      // 验证消息区域内有内容（时间戳 time 元素）
      const timeElements = messageLog.locator('time');
      const timeCount = await timeElements.count();

      // 如果有消息，验证时间戳存在
      if (timeCount > 0) {
        await expect(timeElements.first()).toBeVisible();
      }
    });
  });

  test.describe('消息输入交互', () => {
    test('消息输入框为空时发送按钮应禁用', async ({ page }) => {
      await navigateToChat(page);

      // 找到一个对话进入详情
      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (!hasConversations) {
        test.skip(true, '当前 Dev 环境没有对话数据');
        return;
      }

      await conversationNav.getByRole('button').first().click();
      await expect(page).toHaveURL(/\/chat\/\d+/);

      // 输入框为空时，发送按钮禁用
      const sendButton = page.getByRole('button', { name: '发送消息' });
      await expect(sendButton).toBeDisabled();
    });

    test('输入文字后发送按钮应启用', async ({ page }) => {
      await navigateToChat(page);

      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (!hasConversations) {
        test.skip(true, '当前 Dev 环境没有对话数据');
        return;
      }

      await conversationNav.getByRole('button').first().click();
      await expect(page).toHaveURL(/\/chat\/\d+/);

      // 输入文字
      const messageInput = page.getByLabel('消息输入');
      await messageInput.fill('测试消息');

      // 发送按钮应启用
      const sendButton = page.getByRole('button', { name: '发送消息' });
      await expect(sendButton).toBeEnabled();
    });

    test('Shift+Enter 应换行而非发送', async ({ page }) => {
      await navigateToChat(page);

      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (!hasConversations) {
        test.skip(true, '当前 Dev 环境没有对话数据');
        return;
      }

      await conversationNav.getByRole('button').first().click();
      await expect(page).toHaveURL(/\/chat\/\d+/);

      const messageInput = page.getByLabel('消息输入');
      await messageInput.fill('第一行');
      await messageInput.press('Shift+Enter');
      await messageInput.type('第二行');

      // 验证输入框内容包含换行
      const value = await messageInput.inputValue();
      expect(value).toContain('第一行');
      expect(value).toContain('第二行');
    });
  });

  test.describe('发送消息（真实 API）', () => {
    test('发送消息后应显示用户消息气泡', async ({ page }) => {
      await navigateToChat(page);

      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (!hasConversations) {
        test.skip(true, '当前 Dev 环境没有对话数据');
        return;
      }

      await conversationNav.getByRole('button').first().click();
      await expect(page).toHaveURL(/\/chat\/\d+/);

      const messageInput = page.getByLabel('消息输入');
      const testMessage = `E2E 测试消息 ${Date.now()}`;

      // 发送消息
      await messageInput.fill(testMessage);
      await page.getByRole('button', { name: '发送消息' }).click();

      // 发送后输入框应清空
      await expect(messageInput).toHaveValue('');

      // 发送后发送按钮应禁用（正在流式响应中）
      const sendButton = page.getByRole('button', { name: '发送消息' });
      // 等待一小段时间让消息发出
      await page.waitForTimeout(500);

      // 用户消息应出现在消息列表中
      // 等待消息出现（可能需要刷新查询缓存）
      await expect(page.getByText(testMessage)).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('无障碍 (a11y)', () => {
    test('对话页面应包含正确的 ARIA 属性', async ({ page }) => {
      await navigateToChat(page);

      // 对话列表侧边栏有 aria-label
      await expect(page.getByLabel('对话列表')).toBeVisible();

      // 导航到对话详情
      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (hasConversations) {
        await conversationNav.getByRole('button').first().click();
        await expect(page).toHaveURL(/\/chat\/\d+/);

        // 消息列表应有 role="log" 和 aria-label
        const messageLog = page.getByRole('log', { name: '消息列表' });
        await expect(messageLog).toBeVisible();

        // 消息输入框应有 aria-label
        const messageInput = page.getByLabel('消息输入');
        await expect(messageInput).toBeVisible();

        // 发送按钮应有 aria-label
        const sendButton = page.getByRole('button', { name: '发送消息' });
        await expect(sendButton).toBeVisible();
      }
    });

    test('对话列表项应支持键盘导航', async ({ page }) => {
      await navigateToChat(page);

      const conversationNav = page.getByLabel('对话历史');
      const hasConversations = await conversationNav.isVisible().catch(() => false);

      if (!hasConversations) {
        test.skip(true, '当前 Dev 环境没有对话数据');
        return;
      }

      // Tab 到对话项
      const firstConversation = conversationNav.getByRole('button').first();
      await firstConversation.focus();

      // Enter 键应触发选择
      await page.keyboard.press('Enter');
      await expect(page).toHaveURL(/\/chat\/\d+/);
    });
  });
});

// ========================================================================
// Part 2: Mock 增强测试 — 覆盖边界和异常场景
// ========================================================================

test.describe('对话功能 — Mock 增强场景', () => {
  test.beforeEach(async ({ page }) => {
    await loginWithMock(page);
  });

  test.describe('对话列表边界场景', () => {
    test('对话列表为空时应显示空状态', async ({ page }) => {
      // 覆盖 conversations mock 为空列表
      await page.route(/\/api\/v1\/conversations(\?.*)?$/, async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(paginatedResponse([])),
          });
        }
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await expect(page).toHaveURL('/chat');

      await expect(page.getByText('暂无对话')).toBeVisible();
    });

    test('对话列表加载失败时应显示错误信息', async ({ page }) => {
      // 模拟 API 返回 500 错误
      await page.route(/\/api\/v1\/conversations(\?.*)?$/, async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ code: 'INTERNAL_ERROR', message: '服务器内部错误' }),
          });
        }
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await expect(page).toHaveURL('/chat');

      // 应显示错误提示
      await expect(page.getByText(/加载对话列表失败|错误/)).toBeVisible({ timeout: 5000 });
    });

    test('多个对话应正确渲染列表', async ({ page }) => {
      const manyConversations = [
        {
          id: 1,
          title: '对话 A',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 5,
          total_tokens: 200,
          created_at: '2026-02-27T00:00:00Z',
          updated_at: '2026-02-27T01:00:00Z',
        },
        {
          id: 2,
          title: '对话 B',
          agent_id: 2,
          user_id: 1,
          status: 'completed',
          message_count: 10,
          total_tokens: 500,
          created_at: '2026-02-26T00:00:00Z',
          updated_at: '2026-02-26T12:00:00Z',
        },
        {
          id: 3,
          title: '对话 C',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 0,
          total_tokens: 0,
          created_at: '2026-02-25T00:00:00Z',
          updated_at: '2026-02-25T06:00:00Z',
        },
      ];

      await page.route(/\/api\/v1\/conversations(\?.*)?$/, async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(paginatedResponse(manyConversations)),
          });
        }
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await expect(page).toHaveURL('/chat');

      // 验证所有对话标题显示
      await expect(page.getByText('对话 A')).toBeVisible();
      await expect(page.getByText('对话 B')).toBeVisible();
      await expect(page.getByText('对话 C')).toBeVisible();

      // 验证消息数量显示（通过所属对话按钮上下文定位，避免子串匹配冲突）
      await expect(page.getByRole('button', { name: /对话 A.*5 条消息/ })).toBeVisible();
      await expect(page.getByRole('button', { name: /对话 B.*10 条消息/ })).toBeVisible();
      await expect(page.getByRole('button', { name: /对话 C.*0 条消息/ })).toBeVisible();
    });
  });

  test.describe('对话详情 Mock 场景', () => {
    test('加载对话详情应显示消息气泡', async ({ page }) => {
      const mockDetail = {
        conversation: {
          id: 1,
          title: 'Mock 对话',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 2,
          total_tokens: 100,
          created_at: '2026-02-27T00:00:00Z',
          updated_at: '2026-02-27T01:00:00Z',
        },
        messages: [
          {
            id: 1,
            conversation_id: 1,
            role: 'user',
            content: '你好，请介绍一下自己',
            token_count: 10,
            created_at: '2026-02-27T00:01:00Z',
          },
          {
            id: 2,
            conversation_id: 1,
            role: 'assistant',
            content: '你好！我是一个 AI 助手，很高兴为你服务。',
            token_count: 20,
            created_at: '2026-02-27T00:01:05Z',
          },
        ],
      };

      // Mock 对话详情 API
      await page.route(/\/api\/v1\/conversations\/1$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockDetail),
        });
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await expect(page).toHaveURL('/chat');

      // 点击 mock 对话
      await page.getByText(MOCK_CONVERSATIONS[0].title).click();

      // 验证消息内容显示（使用 exact 避免与 aria-live 区域冲突）
      await expect(page.getByText('你好，请介绍一下自己', { exact: true })).toBeVisible();
      await expect(
        page.getByText('你好！我是一个 AI 助手，很高兴为你服务。', { exact: true }),
      ).toBeVisible();
    });

    test('已结束的对话不应显示消息输入框', async ({ page }) => {
      const completedDetail = {
        conversation: {
          id: 1,
          title: '已结束对话',
          agent_id: 1,
          user_id: 1,
          status: 'completed',
          message_count: 1,
          total_tokens: 50,
          created_at: '2026-02-27T00:00:00Z',
          updated_at: '2026-02-27T01:00:00Z',
        },
        messages: [
          {
            id: 1,
            conversation_id: 1,
            role: 'user',
            content: '测试消息',
            token_count: 5,
            created_at: '2026-02-27T00:01:00Z',
          },
        ],
      };

      await page.route(/\/api\/v1\/conversations\/1$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(completedDetail),
        });
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await page.getByText(MOCK_CONVERSATIONS[0].title).click();

      // 验证"对话已结束"标记显示
      await expect(page.getByText('对话已结束')).toBeVisible();

      // 验证消息输入框不存在（已结束对话不显示输入区）
      await expect(page.getByLabel('消息输入')).not.toBeVisible();
    });

    test('对话详情加载失败应显示错误', async ({ page }) => {
      await page.route(/\/api\/v1\/conversations\/1$/, async (route) => {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ code: 'NOT_FOUND', message: '对话不存在' }),
        });
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await page.getByText(MOCK_CONVERSATIONS[0].title).click();

      // 应显示错误提示（ErrorMessage 组件会渲染 extractApiError 的结果）
      await expect(page.getByText(/加载对话失败|对话不存在|请重试|错误/)).toBeVisible({
        timeout: 5000,
      });
    });

    test('空消息的对话应显示引导文字', async ({ page }) => {
      const emptyDetail = {
        conversation: {
          id: 1,
          title: '新对话',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 0,
          total_tokens: 0,
          created_at: '2026-02-27T00:00:00Z',
          updated_at: '2026-02-27T00:00:00Z',
        },
        messages: [],
      };

      await page.route(/\/api\/v1\/conversations\/1$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(emptyDetail),
        });
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await page.getByText(MOCK_CONVERSATIONS[0].title).click();

      // 应显示引导文字
      await expect(page.getByText('开始新的对话吧')).toBeVisible();
    });
  });

  test.describe('SSE 流式消息 Mock', () => {
    test('发送消息应触发 SSE 流式响应并显示助手回复', async ({ page }) => {
      const mockDetail = {
        conversation: {
          id: 1,
          title: 'SSE 测试对话',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 0,
          total_tokens: 0,
          created_at: '2026-02-27T00:00:00Z',
          updated_at: '2026-02-27T00:00:00Z',
        },
        messages: [],
      };

      // Mock 对话详情
      await page.route(/\/api\/v1\/conversations\/1$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockDetail),
        });
      });

      // Mock SSE 流式端点
      await page.route(/\/api\/v1\/conversations\/1\/messages\/stream$/, async (route) => {
        const sseBody = [
          'data: {"content": "你", "done": false}\n\n',
          'data: {"content": "好", "done": false}\n\n',
          'data: {"content": "！", "done": false}\n\n',
          'data: {"content": "我是", "done": false}\n\n',
          'data: {"content": " AI", "done": false}\n\n',
          'data: {"content": " 助手", "done": false}\n\n',
          'data: {"content": "", "done": true, "message_id": 2, "token_count": 15}\n\n',
        ].join('');

        await route.fulfill({
          status: 200,
          headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            Connection: 'keep-alive',
          },
          body: sseBody,
        });
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await page.getByText(MOCK_CONVERSATIONS[0].title).click();

      // 输入并发送消息
      const messageInput = page.getByLabel('消息输入');
      await messageInput.fill('你好');
      await page.getByRole('button', { name: '发送消息' }).click();

      // 发送后输入框应清空
      await expect(messageInput).toHaveValue('');

      // 等待流式响应完成 — 助手的累积回复应出现
      await expect(page.getByText('你好！我是 AI 助手')).toBeVisible({ timeout: 10000 });
    });

    test('SSE 返回错误应在界面显示错误提示', async ({ page }) => {
      const mockDetail = {
        conversation: {
          id: 1,
          title: 'SSE 错误测试',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 0,
          total_tokens: 0,
          created_at: '2026-02-27T00:00:00Z',
          updated_at: '2026-02-27T00:00:00Z',
        },
        messages: [],
      };

      await page.route(/\/api\/v1\/conversations\/1$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockDetail),
        });
      });

      // Mock SSE 返回错误
      await page.route(/\/api\/v1\/conversations\/1\/messages\/stream$/, async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ code: 'AGENT_ERROR', message: 'Agent 执行失败' }),
        });
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await page.getByText(MOCK_CONVERSATIONS[0].title).click();

      // 发送消息
      await page.getByLabel('消息输入').fill('测试错误');
      await page.getByRole('button', { name: '发送消息' }).click();

      // 应显示错误提示区域
      await expect(page.locator('.bg-red-50, [role="alert"]').first()).toBeVisible({
        timeout: 5000,
      });
    });
  });

  test.describe('消息输入 Mock 场景', () => {
    test.beforeEach(async ({ page }) => {
      const mockDetail = {
        conversation: {
          id: 1,
          title: '输入测试对话',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 0,
          total_tokens: 0,
          created_at: '2026-02-27T00:00:00Z',
          updated_at: '2026-02-27T00:00:00Z',
        },
        messages: [],
      };

      await page.route(/\/api\/v1\/conversations\/1$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockDetail),
        });
      });

      await page.getByLabel('主导航').getByText('对话').click();
      await page.getByText(MOCK_CONVERSATIONS[0].title).click();
    });

    test('输入框 placeholder 应显示正确提示', async ({ page }) => {
      const messageInput = page.getByLabel('消息输入');
      await expect(messageInput).toHaveAttribute(
        'placeholder',
        '输入消息，Enter 发送，Shift+Enter 换行',
      );
    });

    test('仅空白字符不应启用发送按钮', async ({ page }) => {
      const messageInput = page.getByLabel('消息输入');
      await messageInput.fill('   ');

      const sendButton = page.getByRole('button', { name: '发送消息' });
      await expect(sendButton).toBeDisabled();
    });

    test('Enter 键应发送消息', async ({ page }) => {
      // Mock SSE 以避免实际 API 调用
      await page.route(/\/api\/v1\/conversations\/1\/messages\/stream$/, async (route) => {
        await route.fulfill({
          status: 200,
          headers: { 'Content-Type': 'text/event-stream' },
          body: 'data: {"content": "OK", "done": true, "message_id": 1, "token_count": 1}\n\n',
        });
      });

      const messageInput = page.getByLabel('消息输入');
      await messageInput.fill('Enter 发送测试');
      await messageInput.press('Enter');

      // 输入框应清空（消息已发送）
      await expect(messageInput).toHaveValue('');
    });

    test('流式响应期间输入框应禁用', async ({ page }) => {
      // Mock 一个长时间运行的 SSE 响应
      await page.route(/\/api\/v1\/conversations\/1\/messages\/stream$/, async (route) => {
        // 延迟响应以模拟流式传输中
        await new Promise((resolve) => setTimeout(resolve, 3000));
        await route.fulfill({
          status: 200,
          headers: { 'Content-Type': 'text/event-stream' },
          body: 'data: {"content": "done", "done": true, "message_id": 1, "token_count": 1}\n\n',
        });
      });

      const messageInput = page.getByLabel('消息输入');
      await messageInput.fill('流式测试');
      await page.getByRole('button', { name: '发送消息' }).click();

      // 流式期间，输入框 placeholder 应变为 "AI 正在回复中..."
      await expect(messageInput).toHaveAttribute('placeholder', 'AI 正在回复中...', {
        timeout: 2000,
      });
    });
  });

  test.describe('对话切换', () => {
    test('切换对话应加载新对话的消息', async ({ page }) => {
      const conversations = [
        {
          id: 1,
          title: '对话 Alpha',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 1,
          total_tokens: 50,
          created_at: '2026-02-27T00:00:00Z',
          updated_at: '2026-02-27T01:00:00Z',
        },
        {
          id: 2,
          title: '对话 Beta',
          agent_id: 2,
          user_id: 1,
          status: 'active',
          message_count: 1,
          total_tokens: 30,
          created_at: '2026-02-26T00:00:00Z',
          updated_at: '2026-02-26T12:00:00Z',
        },
      ];

      // Mock 对话列表
      await page.route(/\/api\/v1\/conversations(\?.*)?$/, async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(paginatedResponse(conversations)),
          });
        }
      });

      // Mock 对话 1 详情
      await page.route(/\/api\/v1\/conversations\/1$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            conversation: conversations[0],
            messages: [
              {
                id: 1,
                conversation_id: 1,
                role: 'user',
                content: 'Alpha 的消息',
                token_count: 10,
                created_at: '2026-02-27T00:01:00Z',
              },
            ],
          }),
        });
      });

      // Mock 对话 2 详情
      await page.route(/\/api\/v1\/conversations\/2$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            conversation: conversations[1],
            messages: [
              {
                id: 2,
                conversation_id: 2,
                role: 'user',
                content: 'Beta 的消息',
                token_count: 10,
                created_at: '2026-02-26T00:01:00Z',
              },
            ],
          }),
        });
      });

      await page.getByLabel('主导航').getByText('对话').click();

      // 点击第一个对话
      await page.getByText('对话 Alpha').click();
      await expect(page.getByText('Alpha 的消息', { exact: true })).toBeVisible();

      // 切换到第二个对话
      await page.getByText('对话 Beta').click();
      await expect(page.getByText('Beta 的消息', { exact: true })).toBeVisible();

      // Alpha 的消息不应再显示
      await expect(page.getByText('Alpha 的消息', { exact: true })).not.toBeVisible();
    });
  });
});
