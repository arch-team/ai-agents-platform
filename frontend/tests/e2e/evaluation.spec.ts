import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS, MOCK_TEST_SUITES } from './fixtures/mock-data';

test.describe('评估管理', () => {
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('评估列表页应显示正确标题和创建按钮', async ({ page }) => {
    await page.getByLabel('主导航').getByText('评估').click();
    await expect(page).toHaveURL('/evaluation');

    await expect(page.getByRole('heading', { name: '评估管理' })).toBeVisible();
    await expect(page.getByRole('button', { name: '创建测试集' })).toBeVisible();
  });

  test('应显示测试集列表', async ({ page }) => {
    await page.getByLabel('主导航').getByText('评估').click();
    await expect(page).toHaveURL('/evaluation');

    for (const suite of MOCK_TEST_SUITES) {
      await expect(page.getByText(suite.name)).toBeVisible();
    }
  });

  test('应显示状态筛选下拉框', async ({ page }) => {
    await page.getByLabel('主导航').getByText('评估').click();
    await expect(page).toHaveURL('/evaluation');

    await expect(page.getByLabel('状态筛选')).toBeVisible();
  });

  test('测试集列表为空时应显示空状态', async ({ page }) => {
    await page.route(/\/api\/v1\/test-suites(\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
        });
      }
    });

    await page.getByLabel('主导航').getByText('评估').click();
    await expect(page).toHaveURL('/evaluation');

    await expect(page.getByText('暂无测试集')).toBeVisible();
  });

  test('草稿测试集应显示激活和删除按钮', async ({ page }) => {
    await page.getByLabel('主导航').getByText('评估').click();
    await expect(page).toHaveURL('/evaluation');

    // 第二个测试集是 draft 状态
    await expect(
      page.getByRole('button', { name: `激活 ${MOCK_TEST_SUITES[1].name}` }),
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: `删除 ${MOCK_TEST_SUITES[1].name}` }),
    ).toBeVisible();
  });
});
