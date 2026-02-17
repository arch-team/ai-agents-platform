import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS, DASHBOARD_STATS } from './fixtures/mock-data';

test.describe('Dashboard 仪表盘', () => {
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('应显示欢迎标题', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /欢迎回来/ })).toBeVisible();
  });

  test('应显示统计卡片', async ({ page }) => {
    // 验证三个统计卡片标签
    await expect(page.getByText('Agent 总数')).toBeVisible();
    await expect(page.getByText('对话总数')).toBeVisible();
    await expect(page.getByText('Team 执行')).toBeVisible();

    // 验证统计数据
    await expect(page.getByText(String(DASHBOARD_STATS.agents_total))).toBeVisible();
    await expect(page.getByText(String(DASHBOARD_STATS.conversations_total))).toBeVisible();
    await expect(page.getByText(String(DASHBOARD_STATS.team_executions_total))).toBeVisible();
  });

  test('应显示快速操作区域', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '快速操作' })).toBeVisible();

    // 验证快速操作链接
    await expect(page.getByRole('link', { name: /创建 Agent/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /查看 Agent 列表/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /Team Execution/ })).toBeVisible();
  });

  test('点击"创建 Agent"快速操作应导航到创建页面', async ({ page }) => {
    await page.getByRole('link', { name: /创建 Agent/ }).click();
    await expect(page).toHaveURL('/agents/create');
  });
});
