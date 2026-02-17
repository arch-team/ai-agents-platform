import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS, MOCK_CONVERSATIONS } from './fixtures/mock-data';

test.describe('对话功能', () => {
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('对话页面应显示对话列表侧边栏', async ({ page }) => {
    await page.getByLabel('主导航').getByText('对话').click();
    await expect(page).toHaveURL('/chat');

    // 验证对话列表侧边栏
    await expect(page.getByLabel('对话列表')).toBeVisible();
  });

  test('应显示新建对话按钮', async ({ page }) => {
    await page.getByLabel('主导航').getByText('对话').click();
    await expect(page).toHaveURL('/chat');

    await expect(page.getByRole('button', { name: '新建对话' })).toBeVisible();
  });

  test('应显示已有的对话列表', async ({ page }) => {
    await page.getByLabel('主导航').getByText('对话').click();
    await expect(page).toHaveURL('/chat');

    // 验证 mock 对话显示
    for (const conv of MOCK_CONVERSATIONS) {
      await expect(page.getByText(conv.title)).toBeVisible();
    }
  });

  test('未选择对话时应显示提示', async ({ page }) => {
    await page.getByLabel('主导航').getByText('对话').click();
    await expect(page).toHaveURL('/chat');

    await expect(page.getByText('请选择一个对话')).toBeVisible();
  });

  test('对话列表为空时应显示空状态', async ({ page }) => {
    // 覆盖 conversations mock 为空列表
    await page.route(/\/api\/v1\/conversations(\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
        });
      }
    });

    await page.getByLabel('主导航').getByText('对话').click();
    await expect(page).toHaveURL('/chat');

    await expect(page.getByText('暂无对话')).toBeVisible();
  });
});
