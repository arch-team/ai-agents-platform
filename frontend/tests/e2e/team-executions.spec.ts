import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS, MOCK_TEAM_EXECUTIONS } from './fixtures/mock-data';

test.describe('团队执行', () => {
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('应显示新建执行表单', async ({ page }) => {
    await page.getByLabel('主导航').getByText('团队执行').click();
    await expect(page).toHaveURL('/team-executions');

    await expect(page.getByRole('heading', { name: '新建执行' })).toBeVisible();
    await expect(page.getByLabel('选择 Agent')).toBeVisible();
    await expect(page.getByLabel('执行提示词')).toBeVisible();
    await expect(page.getByRole('button', { name: '提交执行' })).toBeVisible();
  });

  test('应显示执行历史列表', async ({ page }) => {
    await page.getByLabel('主导航').getByText('团队执行').click();
    await expect(page).toHaveURL('/team-executions');

    await expect(page.getByRole('heading', { name: '执行历史' })).toBeVisible();

    // 验证 mock 执行记录显示
    for (const exec of MOCK_TEAM_EXECUTIONS) {
      await expect(page.getByText(exec.prompt)).toBeVisible();
    }
  });

  test('执行历史为空时应显示空状态', async ({ page }) => {
    // 覆盖团队执行 mock 为空列表
    await page.route(/\/api\/v1\/team-executions(\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 }),
        });
      }
    });

    await page.getByLabel('主导航').getByText('团队执行').click();
    await expect(page).toHaveURL('/team-executions');

    await expect(page.getByText(/暂无执行记录/)).toBeVisible();
  });

  test('未选择执行记录时应显示右侧提示', async ({ page }) => {
    await page.getByLabel('主导航').getByText('团队执行').click();
    await expect(page).toHaveURL('/team-executions');

    await expect(page.getByText(/选择一个执行记录/)).toBeVisible();
  });
});
