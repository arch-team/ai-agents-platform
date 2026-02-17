import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS, MOCK_TOOLS } from './fixtures/mock-data';

test.describe('工具目录', () => {
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('工具列表页应显示正确标题和注册按钮', async ({ page }) => {
    await page.getByLabel('主导航').getByText('工具目录').click();
    await expect(page).toHaveURL('/tools');

    await expect(page.getByRole('heading', { name: '工具目录' })).toBeVisible();
    await expect(page.getByRole('button', { name: '注册工具' })).toBeVisible();
  });

  test('应显示工具列表', async ({ page }) => {
    await page.getByLabel('主导航').getByText('工具目录').click();
    await expect(page).toHaveURL('/tools');

    for (const tool of MOCK_TOOLS) {
      await expect(page.getByText(tool.name)).toBeVisible();
    }
  });

  test('应显示状态和类型筛选', async ({ page }) => {
    await page.getByLabel('主导航').getByText('工具目录').click();
    await expect(page).toHaveURL('/tools');

    await expect(page.getByLabel('状态')).toBeVisible();
    await expect(page.getByLabel('类型')).toBeVisible();
  });

  test('工具列表为空时应显示空状态', async ({ page }) => {
    await page.route(/\/api\/v1\/tools(\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
        });
      }
    });

    await page.getByLabel('主导航').getByText('工具目录').click();
    await expect(page).toHaveURL('/tools');

    await expect(page.getByText('暂无工具')).toBeVisible();
  });
});
