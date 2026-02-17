import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS } from './fixtures/mock-data';

test.describe('404 页面', () => {
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('访问不存在的路径应显示 404 页面', async ({ page }) => {
    await page.getByLabel('主导航').getByText('仪表盘').click();
    // 使用 JS 导航避免全页刷新丢失内存状态
    await page.evaluate(() => window.history.pushState({}, '', '/non-existent-page'));
    // 触发 React Router 重新渲染
    await page.evaluate(() => window.dispatchEvent(new PopStateEvent('popstate')));

    await expect(page.getByRole('heading', { name: '404' })).toBeVisible();
    await expect(page.getByText('页面未找到')).toBeVisible();
  });

  test('404 页面应有返回首页按钮', async ({ page }) => {
    await page.evaluate(() => window.history.pushState({}, '', '/some-random-path'));
    await page.evaluate(() => window.dispatchEvent(new PopStateEvent('popstate')));

    await expect(page.getByRole('link', { name: '返回首页' })).toBeVisible();
  });
});
