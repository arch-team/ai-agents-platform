import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS, MOCK_AGENTS } from './fixtures/mock-data';

test.describe('Agent 管理流程', () => {
  // 每个测试前先登录获取认证状态，并通过侧边栏导航到 Agent 列表
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('Agent 列表页应显示所有 Agent', async ({ page }) => {
    // 通过侧边栏 SPA 导航到 Agent 列表（避免 page.goto 导致全页刷新丢失内存状态）
    await page.getByLabel('主导航').getByText('Agent 列表').click();
    await expect(page).toHaveURL('/agents');

    // 验证页面标题
    await expect(page.getByRole('heading', { name: 'Agent 管理' })).toBeVisible();

    // 验证每个 mock Agent 都显示
    for (const agent of MOCK_AGENTS) {
      await expect(page.getByText(agent.name)).toBeVisible();
    }
  });

  test('应显示不同状态的 Agent', async ({ page }) => {
    await page.getByLabel('主导航').getByText('Agent 列表').click();
    await expect(page).toHaveURL('/agents');

    // 验证 Agent 卡片上的三种状态标签（使用 locator 过滤掉筛选下拉框中的 option 元素）
    await expect(page.locator('span', { hasText: '草稿' }).first()).toBeVisible();
    await expect(page.locator('span', { hasText: '已激活' }).first()).toBeVisible();
    await expect(page.locator('span', { hasText: '已归档' }).first()).toBeVisible();
  });

  test('创建新 Agent 表单应正确提交', async ({ page }) => {
    // 先导航到 Agent 列表，再通过 "创建 Agent" 按钮进入创建页面
    await page.getByLabel('主导航').getByText('Agent 列表').click();
    await expect(page).toHaveURL('/agents');
    await page.getByRole('button', { name: '创建 Agent' }).click();
    await expect(page).toHaveURL('/agents/create');

    // 验证创建页面标题
    await expect(page.getByRole('heading', { name: '创建 Agent' })).toBeVisible();

    // 填写表单
    await page.getByLabel('名称').fill('测试新 Agent');
    await page.getByLabel('描述').fill('这是一个测试 Agent');
    await page.getByLabel('系统提示词').fill('你是一个测试助手');

    // 提交表单
    await page.getByRole('button', { name: '创建 Agent' }).click();

    // 创建成功后应跳转到详情页
    await expect(page).toHaveURL(/\/agents\/\d+/);
  });

  test('点击 Agent 应导航到详情页', async ({ page }) => {
    // mock 对话列表（详情页需要）
    await page.route('**/api/v1/conversations*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
      });
    });

    await page.getByLabel('主导航').getByText('Agent 列表').click();
    await expect(page).toHaveURL('/agents');

    // 点击第一个 Agent 卡片
    await page.getByRole('button', { name: `查看 Agent: ${MOCK_AGENTS[0].name}` }).click();

    // 应导航到详情页
    await expect(page).toHaveURL(/\/agents\/\d+/);
  });

  test('Agent 详情页应显示配置信息', async ({ page }) => {
    // mock 对话列表（详情页需要）
    await page.route('**/api/v1/conversations*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
      });
    });

    // 通过侧边栏导航到 Agent 列表，再点击第一个 Agent 进入详情页
    await page.getByLabel('主导航').getByText('Agent 列表').click();
    await expect(page).toHaveURL('/agents');
    await page.getByRole('button', { name: `查看 Agent: ${MOCK_AGENTS[0].name}` }).click();
    await expect(page).toHaveURL(/\/agents\/\d+/);

    // 验证 Agent 名称和配置信息标题
    await expect(page.getByRole('heading', { name: MOCK_AGENTS[0].name })).toBeVisible();
    await expect(page.getByText('配置信息')).toBeVisible();

    // 验证配置详情
    await expect(page.getByText(MOCK_AGENTS[0].config.model_id)).toBeVisible();
  });
});
