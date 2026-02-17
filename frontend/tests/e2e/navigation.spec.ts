import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS } from './fixtures/mock-data';

// 侧边栏导航项配置（与 Sidebar.tsx 中 navGroups 对应）
const NAV_ITEMS = [
  { label: '仪表盘', path: '/' },
  { label: 'Agent 列表', path: '/agents' },
  { label: '对话', path: '/chat' },
  { label: '团队执行', path: '/team-executions' },
  { label: '知识库', path: '/knowledge' },
  { label: '模板', path: '/templates' },
  { label: '工具目录', path: '/tools' },
  { label: '使用洞察', path: '/insights' },
  { label: '评估', path: '/evaluation' },
];

test.describe('全局导航', () => {
  // 每个测试前先登录获取认证状态
  test.beforeEach(async ({ page }) => {
    await mockAll(page);

    // mock 所有可能需要的额外 API（导航测试会访问多个页面）
    await page.route('**/api/v1/knowledge-bases*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
      });
    });
    await page.route('**/api/v1/templates*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
      });
    });
    await page.route('**/api/v1/tools*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
      });
    });
    await page.route('**/api/v1/evaluation*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }),
      });
    });

    // 先登录
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('侧边栏应显示所有导航链接', async ({ page }) => {
    const sidebar = page.getByLabel('主导航');
    await expect(sidebar).toBeVisible();

    for (const item of NAV_ITEMS) {
      await expect(sidebar.getByText(item.label)).toBeVisible();
    }
  });

  test('点击侧边栏链接应导航到对应页面', async ({ page }) => {
    const sidebar = page.getByLabel('主导航');

    // 测试几个关键导航项
    const testItems = [
      { label: 'Agent 列表', path: '/agents' },
      { label: '使用洞察', path: '/insights' },
      { label: '知识库', path: '/knowledge' },
    ];

    for (const item of testItems) {
      await sidebar.getByText(item.label).click();
      await expect(page).toHaveURL(item.path);
    }
  });

  test('每个页面应显示正确的页面标题', async ({ page }) => {
    const sidebar = page.getByLabel('主导航');

    // Dashboard 页面（已在登录后默认访问）
    await expect(page.getByRole('heading', { name: /欢迎回来/ })).toBeVisible();

    // Agent 列表页面
    await sidebar.getByText('Agent 列表').click();
    await expect(page.getByRole('heading', { name: 'Agent 管理' })).toBeVisible();
  });

  test('移动端应有汉堡菜单按钮', async ({ page }) => {
    // 设置移动端视口尺寸
    await page.setViewportSize({ width: 375, height: 667 });

    // 汉堡菜单按钮应可见（仅在移动端通过 lg:hidden 显示）
    await expect(page.getByRole('button', { name: '切换菜单' })).toBeVisible();
  });
});
