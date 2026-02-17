import { test, expect } from '@playwright/test';

import { mockAuth } from './helpers/api-mock';
import { LOGIN_CREDENTIALS } from './fixtures/mock-data';

test.describe('认证流程', () => {
  test('未认证时访问根路径应重定向到 /login', async ({ page }) => {
    // 不设置任何 mock，模拟未认证状态
    // mock /auth/me 返回 401，确保未认证
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({ status: 401, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('登录页面应正确渲染', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByRole('heading', { name: '登录' })).toBeVisible();
    await expect(page.getByLabel('邮箱')).toBeVisible();
    await expect(page.getByLabel('密码')).toBeVisible();
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible();
  });

  test('使用正确凭证登录应跳转到 Dashboard', async ({ page }) => {
    await mockAuth(page);

    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();

    // 登录成功后应跳转到首页 Dashboard
    await expect(page).toHaveURL('/');
  });

  test('使用错误凭证登录应显示错误信息', async ({ page }) => {
    // mock /auth/me 返回 401（未登录状态）
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({ status: 401, contentType: 'application/json', body: '{}' });
    });

    // mock /auth/login 返回 401
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: '邮箱或密码错误' }),
      });
    });

    await page.goto('/login');
    await page.getByLabel('邮箱').fill('wrong@example.com');
    await page.getByLabel('密码').fill('WrongPass1');
    await page.getByRole('button', { name: '登录' }).click();

    // 应显示错误提示
    await expect(page.getByRole('alert')).toBeVisible();
  });

  test('登出功能应跳转回登录页', async ({ page }) => {
    await mockAuth(page);

    // mock Dashboard API（登录后首页需要）
    await page.route('**/api/v1/insights/summary*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });
    await page.route('**/api/v1/stats/summary*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });
    await page.route('**/api/v1/insights/cost-breakdown*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });
    await page.route('**/api/v1/insights/usage-trends*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    // 先走登录流程获取认证状态
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');

    // 确保登出按钮可见后点击
    await expect(page.getByRole('button', { name: '登出' })).toBeVisible();
    await page.getByRole('button', { name: '登出' }).click();
    await expect(page).toHaveURL(/\/login/);
  });
});
