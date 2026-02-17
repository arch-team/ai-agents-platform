import { test, expect } from '@playwright/test';

test.describe('注册流程', () => {
  test.beforeEach(async ({ page }) => {
    // mock /auth/me 返回 401（未登录状态）
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({ status: 401, contentType: 'application/json', body: '{}' });
    });
  });

  test('注册页面应正确渲染', async ({ page }) => {
    await page.goto('/register');

    await expect(page.getByRole('heading', { name: '注册' })).toBeVisible();
    await expect(page.getByLabel('姓名')).toBeVisible();
    await expect(page.getByLabel('邮箱')).toBeVisible();
    await expect(page.getByLabel('密码', { exact: true })).toBeVisible();
    await expect(page.getByLabel('确认密码')).toBeVisible();
    await expect(page.getByRole('button', { name: '注册' })).toBeVisible();
  });

  test('应有跳转登录页面的链接', async ({ page }) => {
    await page.goto('/register');

    const loginLink = page.getByRole('link', { name: /立即登录/ });
    await expect(loginLink).toBeVisible();
    await loginLink.click();
    await expect(page).toHaveURL(/\/login/);
  });

  test('注册成功应跳转到登录页面', async ({ page }) => {
    // mock 注册 API 返回成功
    await page.route('**/api/v1/auth/register', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ message: '注册成功' }),
      });
    });

    await page.goto('/register');
    await page.getByLabel('姓名').fill('新用户');
    await page.getByLabel('邮箱').fill('new@example.com');
    await page.getByLabel('密码', { exact: true }).fill('Password1');
    await page.getByLabel('确认密码').fill('Password1');
    await page.getByRole('button', { name: '注册' }).click();

    // 注册成功后应跳转到登录页
    await expect(page).toHaveURL(/\/login/);
  });

  test('注册失败应显示错误信息', async ({ page }) => {
    // mock 注册 API 返回 409（邮箱已存在）
    await page.route('**/api/v1/auth/register', async (route) => {
      await route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ detail: '该邮箱已注册' }),
      });
    });

    await page.goto('/register');
    await page.getByLabel('姓名').fill('新用户');
    await page.getByLabel('邮箱').fill('existing@example.com');
    await page.getByLabel('密码', { exact: true }).fill('Password1');
    await page.getByLabel('确认密码').fill('Password1');
    await page.getByRole('button', { name: '注册' }).click();

    // 应显示错误提示
    await expect(page.getByRole('alert')).toBeVisible();
  });
});
