import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS, MOCK_TEMPLATES } from './fixtures/mock-data';

test.describe('模板管理', () => {
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('模板列表页应显示正确标题和创建按钮', async ({ page }) => {
    await page.getByLabel('主导航').getByText('模板').click();
    await expect(page).toHaveURL('/templates');

    await expect(page.getByRole('heading', { name: '模板管理' })).toBeVisible();
    await expect(page.getByRole('button', { name: '创建模板' })).toBeVisible();
  });

  test('应显示模板列表', async ({ page }) => {
    await page.getByLabel('主导航').getByText('模板').click();
    await expect(page).toHaveURL('/templates');

    for (const template of MOCK_TEMPLATES) {
      await expect(page.getByText(template.name)).toBeVisible();
    }
  });

  test('应显示状态筛选下拉框', async ({ page }) => {
    await page.getByLabel('主导航').getByText('模板').click();
    await expect(page).toHaveURL('/templates');

    await expect(page.getByLabel('状态')).toBeVisible();
  });

  test('模板列表为空时应显示空状态', async ({ page }) => {
    await page.route(/\/api\/v1\/templates(\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
        });
      }
    });

    await page.getByLabel('主导航').getByText('模板').click();
    await expect(page).toHaveURL('/templates');

    await expect(page.getByText('暂无模板')).toBeVisible();
  });

  test('草稿模板应显示删除按钮', async ({ page }) => {
    await page.getByLabel('主导航').getByText('模板').click();
    await expect(page).toHaveURL('/templates');

    // 第二个模板是 draft 状态
    await expect(
      page.getByRole('button', { name: `删除 ${MOCK_TEMPLATES[1].name}` }),
    ).toBeVisible();
  });
});
