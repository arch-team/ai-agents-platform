import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS, MOCK_KNOWLEDGE_BASES } from './fixtures/mock-data';

test.describe('知识库管理', () => {
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('知识库列表页应显示正确标题和创建按钮', async ({ page }) => {
    await page.getByLabel('主导航').getByText('知识库').click();
    await expect(page).toHaveURL('/knowledge');

    await expect(page.getByRole('heading', { name: '知识库管理' })).toBeVisible();
    await expect(page.getByRole('button', { name: '创建知识库' })).toBeVisible();
  });

  test('应显示知识库列表', async ({ page }) => {
    await page.getByLabel('主导航').getByText('知识库').click();
    await expect(page).toHaveURL('/knowledge');

    for (const kb of MOCK_KNOWLEDGE_BASES) {
      await expect(page.getByText(kb.name)).toBeVisible();
    }
  });

  test('应显示状态筛选下拉框', async ({ page }) => {
    await page.getByLabel('主导航').getByText('知识库').click();
    await expect(page).toHaveURL('/knowledge');

    await expect(page.getByLabel('状态筛选')).toBeVisible();
  });

  test('知识库列表为空时应显示空状态', async ({ page }) => {
    // 覆盖知识库 mock 为空列表
    await page.route(/\/api\/v1\/knowledge-bases(\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
        });
      }
    });

    await page.getByLabel('主导航').getByText('知识库').click();
    await expect(page).toHaveURL('/knowledge');

    await expect(page.getByText('暂无知识库')).toBeVisible();
  });

  test('ACTIVE 状态的知识库应显示同步按钮', async ({ page }) => {
    await page.getByLabel('主导航').getByText('知识库').click();
    await expect(page).toHaveURL('/knowledge');

    // 第一个知识库是 active 状态，应有同步按钮
    await expect(
      page.getByRole('button', { name: `同步 ${MOCK_KNOWLEDGE_BASES[0].name}` }),
    ).toBeVisible();
  });
});
