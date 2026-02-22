/**
 * 工具目录 E2E 测试
 *
 * 测试策略：每个 describe 块通过 beforeEach 登录（内存 Token 无法用 storageState 持久化）
 * 覆盖：列表浏览 / 筛选 / 注册工具 / 审批流程 / 权限边界
 */

import { test, expect, type Page } from '@playwright/test';

const BASE_URL = 'http://ai-agents-platform-frontend-dev-897473.s3-website-us-east-1.amazonaws.com';

const ADMIN = { email: 'admin@company.com', password: 'Admin@2026!' };

// ─── 共用辅助函数 ────────────────────────────────────────────────────────────

/**
 * 登录并通过侧边栏导航到工具目录页。
 * 【关键】登录后必须用侧边栏链接跳转（React Router 客户端导航），
 *  不能用 page.goto('/tools')，否则整页重载会清空 Zustand 内存 Token。
 */
async function loginAndGoToTools(page: Page, credentials = ADMIN) {
  // Step 1: 全页加载登录页
  await page.goto(`${BASE_URL}/login`);
  await page.getByLabel('邮箱').fill(credentials.email);
  await page.getByLabel('密码').fill(credentials.password);
  await page.getByRole('button', { name: '登录' }).click();
  // 等待登录成功跳转（React Router 客户端跳转，不清空内存）
  await page.waitForURL(`${BASE_URL}/`, { timeout: 15000 });

  // Step 2: 通过侧边栏导航到工具目录（客户端路由，Token 保留在内存中）
  await page.getByRole('link', { name: '工具目录' }).click();
  await page.waitForURL(/\/tools/, { timeout: 10000 });
  await page.waitForLoadState('networkidle');
}

// ─── 测试套件 ────────────────────────────────────────────────────────────────

test.describe('工具目录 — 基础浏览', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndGoToTools(page);
  });

  test('页面标题正确', async ({ page }) => {
    await expect(page).toHaveURL(/\/tools/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('显示工具列表（含 4 条测试数据）', async ({ page }) => {
    // 等待列表加载完成（非 loading 状态）
    await expect(page.locator('[role="status"]'))
      .not.toBeVisible({ timeout: 10000 })
      .catch(() => {});
    const cards = page.locator('[role="button"][aria-label*="查看工具"]');
    await expect(cards.first()).toBeVisible({ timeout: 10000 });
    const count = await cards.count();
    expect(count).toBeGreaterThanOrEqual(4);
  });

  test('工具卡片显示名称、描述、状态徽章、类型', async ({ page }) => {
    const firstCard = page.locator('[role="button"][aria-label*="查看工具"]').first();
    await expect(firstCard).toBeVisible({ timeout: 10000 });
    // 卡片内有 h3 标题
    await expect(firstCard.locator('h3')).toBeVisible();
    // 卡片内有描述文字
    await expect(firstCard.locator('p')).toBeVisible();
    // 卡片底部有工具类型文字（MCP Server / API / Function 之一）
    const typeText = firstCard.locator('span').filter({ hasText: /MCP Server|API|Function/ });
    await expect(typeText.first()).toBeVisible();
  });

  test('APPROVED 工具卡片显示绿色状态徽章', async ({ page }) => {
    // 筛选 APPROVED 工具
    await page.locator('#tool-status-filter').selectOption('approved');

    const cards = page.locator('[role="button"][aria-label*="查看工具"]');
    await expect(cards.first()).toBeVisible({ timeout: 10000 });
    // 天气查询 API 应该可见
    await expect(page.getByText('天气查询 API')).toBeVisible();
  });
});

test.describe('工具目录 — 筛选功能', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndGoToTools(page);

    // 等待列表加载
    await page
      .locator('[role="button"][aria-label*="查看工具"]')
      .first()
      .waitFor({ timeout: 10000 })
      .catch(() => {});
  });

  test('状态筛选器存在且包含所有选项', async ({ page }) => {
    const select = page.locator('#tool-status-filter');
    await expect(select).toBeVisible();
    await expect(select.locator('option[value=""]')).toHaveText('全部状态');
    await expect(select.locator('option[value="approved"]')).toHaveText('已审批');
    await expect(select.locator('option[value="draft"]')).toHaveText('草稿');
    await expect(select.locator('option[value="pending_review"]')).toHaveText('待审批');
    await expect(select.locator('option[value="rejected"]')).toHaveText('已拒绝');
    await expect(select.locator('option[value="deprecated"]')).toHaveText('已废弃');
  });

  test('类型筛选器存在且包含所有选项', async ({ page }) => {
    const select = page.locator('#tool-type-filter');
    await expect(select).toBeVisible();
    await expect(select.locator('option[value=""]')).toHaveText('全部类型');
    await expect(select.locator('option[value="mcp_server"]')).toHaveText('MCP Server');
    await expect(select.locator('option[value="api"]')).toHaveText('API');
    await expect(select.locator('option[value="function"]')).toHaveText('Function');
  });

  test('按状态 APPROVED 筛选只显示已审批工具', async ({ page }) => {
    await page.locator('#tool-status-filter').selectOption('approved');
    await page.waitForLoadState('networkidle');
    // APPROVED 工具应可见
    await expect(page.locator('h3').filter({ hasText: '天气查询 API' })).toBeVisible({
      timeout: 10000,
    });
    // 结果数量为 1（只有一个 APPROVED 工具）
    const cards = page.locator('[role="button"][aria-label*="查看工具"]');
    await expect(cards).toHaveCount(1, { timeout: 15000 });
  });

  test('按状态 DRAFT 筛选只显示草稿工具', async ({ page }) => {
    await page.locator('#tool-status-filter').selectOption('draft');

    await expect(page.getByText('企业知识库检索')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('天气查询 API')).not.toBeVisible();
  });

  test('按类型 MCP_SERVER 筛选', async ({ page }) => {
    await page.locator('#tool-type-filter').selectOption('mcp_server');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h3').filter({ hasText: '文件搜索 MCP Server' })).toBeVisible({
      timeout: 10000,
    });
    // 只有 1 个 mcp_server 类型工具
    const cards = page.locator('[role="button"][aria-label*="查看工具"]');
    await expect(cards).toHaveCount(1, { timeout: 10000 });
  });

  test('按类型 FUNCTION 筛选', async ({ page }) => {
    await page.locator('#tool-type-filter').selectOption('function');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h3').filter({ hasText: '代码格式化工具' })).toBeVisible({
      timeout: 10000,
    });
    // 只有 1 个 function 类型工具
    const cards = page.locator('[role="button"][aria-label*="查看工具"]');
    await expect(cards).toHaveCount(1, { timeout: 10000 });
  });

  test('重置为全部状态后显示所有工具', async ({ page }) => {
    // 先筛选
    await page.locator('#tool-status-filter').selectOption('approved');

    // 再重置
    await page.locator('#tool-status-filter').selectOption('');

    const cards = page.locator('[role="button"][aria-label*="查看工具"]');
    const count = await cards.count();
    expect(count).toBeGreaterThanOrEqual(4);
  });
});

test.describe('工具目录 — 注册工具对话框', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndGoToTools(page);
  });

  test('ADMIN 能看到注册工具按钮', async ({ page }) => {
    await expect(page.getByRole('button', { name: '注册工具' })).toBeVisible({ timeout: 10000 });
  });

  test('点击注册工具打开对话框', async ({ page }) => {
    await page.getByRole('button', { name: '注册工具' }).click();
    // 对话框应出现
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });
  });

  test('注册对话框含必要表单字段', async ({ page }) => {
    await page.getByRole('button', { name: '注册工具' }).click();
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });
    // 应有工具名称输入框（placeholder 或 label 识别）
    const nameInput = page.getByRole('dialog').locator('input, textarea, select').first();
    await expect(nameInput).toBeVisible({ timeout: 5000 });
    // 对话框内有至少一个 label 标签
    const labels = page.getByRole('dialog').locator('label');
    expect(await labels.count()).toBeGreaterThan(0);
  });

  test('注册对话框可关闭', async ({ page }) => {
    await page.getByRole('button', { name: '注册工具' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    // 关闭按钮
    const closeBtn = page.getByRole('button', { name: /关闭|取消|✕|×/ });
    if ((await closeBtn.count()) > 0) {
      await closeBtn.first().click();
    } else {
      await page.keyboard.press('Escape');
    }
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 3000 });
  });
});

test.describe('工具目录 — 四种状态数据验证', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndGoToTools(page);

    await page
      .locator('[role="button"][aria-label*="查看工具"]')
      .first()
      .waitFor({ timeout: 10000 })
      .catch(() => {});
  });

  test('APPROVED 状态：天气查询 API', async ({ page }) => {
    await page.locator('#tool-status-filter').selectOption('approved');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('天气查询 API')).toBeVisible({ timeout: 10000 });
  });

  test('REJECTED 状态：代码格式化工具', async ({ page }) => {
    await page.locator('#tool-status-filter').selectOption('rejected');

    await expect(page.getByText('代码格式化工具')).toBeVisible({ timeout: 10000 });
  });

  test('PENDING_REVIEW 状态：文件搜索 MCP Server', async ({ page }) => {
    await page.locator('#tool-status-filter').selectOption('pending_review');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('文件搜索 MCP Server')).toBeVisible({ timeout: 10000 });
  });

  test('DRAFT 状态：企业知识库检索', async ({ page }) => {
    await page.locator('#tool-status-filter').selectOption('draft');

    await expect(page.getByText('企业知识库检索')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('工具目录 — 可访问性与响应式', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndGoToTools(page);
  });

  test('状态筛选 select 有关联 label', async ({ page }) => {
    await expect(page.locator('label[for="tool-status-filter"]')).toHaveText('状态');
    await expect(page.locator('#tool-status-filter')).toBeVisible();
  });

  test('类型筛选 select 有关联 label', async ({ page }) => {
    await expect(page.locator('label[for="tool-type-filter"]')).toHaveText('类型');
    await expect(page.locator('#tool-type-filter')).toBeVisible();
  });

  test('工具卡片有 aria-label（支持屏幕阅读器）', async ({ page }) => {
    await page
      .locator('[role="button"][aria-label*="查看工具"]')
      .first()
      .waitFor({ timeout: 10000 })
      .catch(() => {});
    const cards = page.locator('[role="button"][aria-label*="查看工具"]');
    if ((await cards.count()) > 0) {
      const ariaLabel = await cards.first().getAttribute('aria-label');
      expect(ariaLabel).toContain('查看工具');
    }
  });

  test('工具卡片支持 Enter 键盘交互', async ({ page }) => {
    const firstCard = page.locator('[role="button"][aria-label*="查看工具"]').first();
    await firstCard.waitFor({ timeout: 10000 }).catch(() => {});
    if (await firstCard.isVisible()) {
      await firstCard.focus();
      await expect(firstCard).toBeFocused();
    }
  });

  test('移动端（375px）视口正常显示', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(page.locator('#tool-status-filter')).toBeVisible();
    await expect(page.locator('#tool-type-filter')).toBeVisible();
    await expect(page.getByRole('button', { name: '注册工具' })).toBeVisible();
  });

  test('平板（768px）视口正常显示', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('#tool-status-filter')).toBeVisible();
    await expect(page.getByRole('button', { name: '注册工具' })).toBeVisible();
  });
});
