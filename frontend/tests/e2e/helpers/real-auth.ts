/**
 * 真实环境 E2E 测试认证辅助函数
 *
 * 关键约束：Token 存储在 Zustand 内存中（非 localStorage），
 * page.goto() 全页重载会清空 Token。登录后必须通过侧边栏客户端导航。
 */
import type { Page } from '@playwright/test';

/** Dev 环境基础 URL */
export const DEV_BASE_URL = 'https://d2k7ovgb2e4af9.cloudfront.net';

/** 测试用管理员账户 */
export const ADMIN_CREDENTIALS = {
  email: 'admin@company.com',
  password: 'Admin@2026!',
};

/**
 * 登录到真实 Dev 环境
 * 登录成功后会跳转到仪表板页面 (/)
 */
export async function loginToDevEnv(page: Page, credentials = ADMIN_CREDENTIALS): Promise<void> {
  await page.goto(`${DEV_BASE_URL}/login`);
  await page.getByLabel('邮箱').fill(credentials.email);
  await page.getByLabel('密码').fill(credentials.password);
  // exact: true 避免匹配到 "企业 SSO 登录" 按钮
  await page.getByRole('button', { name: '登录', exact: true }).click();
  // SPA 导航使用 domcontentloaded 而非 load（React Router 不触发 load 事件）
  // 增大超时防止频繁登录时 API Rate Limiting
  await page.waitForURL(`${DEV_BASE_URL}/`, {
    timeout: 25_000,
    waitUntil: 'domcontentloaded',
  });
}

/**
 * 通过侧边栏导航到指定页面（保持内存 Token）
 *
 * 重要：登录后不能用 page.goto()，必须通过侧边栏客户端路由导航，
 * 否则全页重载会清空 Zustand 内存中的 Token。
 */
export async function navigateViaSidebar(
  page: Page,
  menuText: string,
  expectedPath: string,
): Promise<void> {
  await page.getByLabel('主导航').getByText(menuText).click();
  await page.waitForURL(`${DEV_BASE_URL}${expectedPath}`, {
    timeout: 15_000,
    waitUntil: 'domcontentloaded',
  });
}

/**
 * 登录并导航到目标页面的组合辅助函数
 */
export async function loginAndNavigateTo(
  page: Page,
  menuText: string,
  expectedPath: string,
  credentials = ADMIN_CREDENTIALS,
): Promise<void> {
  await loginToDevEnv(page, credentials);
  await navigateViaSidebar(page, menuText, expectedPath);
}

/**
 * 等待 API 请求完成的辅助函数
 */
export async function waitForApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  options: { status?: number; timeout?: number } = {},
): Promise<void> {
  const { status = 200, timeout = 15_000 } = options;
  await page.waitForResponse(
    (resp) => {
      const matches =
        typeof urlPattern === 'string'
          ? resp.url().includes(urlPattern)
          : urlPattern.test(resp.url());
      return matches && resp.status() === status;
    },
    { timeout },
  );
}

/**
 * 截图辅助函数 — 保存到 test-results/screenshots/ 目录
 */
export async function takeScreenshot(page: Page, name: string): Promise<void> {
  await page.screenshot({
    path: `test-results/screenshots/${name}.png`,
    fullPage: true,
  });
}
