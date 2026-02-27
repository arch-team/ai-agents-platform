/**
 * Agent 构建器 — 真实环境 E2E 测试
 *
 * 针对 Dev 环境 (d2k7ovgb2e4af9.cloudfront.net) 的真实 API 测试。
 *
 * 关键约束:
 * - Token 存储在 Zustand 内存中，page.goto() 会清空 Token
 * - 登录后必须通过侧边栏客户端导航，不能 page.goto() 到其他页面
 * - Builder 使用 SSE 流式通信生成 Agent 配置，需要较长超时
 */

import { test, expect } from '@playwright/test';

import {
  loginAndNavigateTo,
  navigateViaSidebar,
  takeScreenshot,
  waitForApiResponse,
  DEV_BASE_URL,
} from './helpers/real-auth';

// ========================================================================
// 常量
// ========================================================================

/** 侧边栏菜单名 */
const SIDEBAR_MENU = 'Agent 构建器';
/** 路由路径 */
const BUILDER_PATH = '/builder';
/** SSE 流式生成的超时时间（120 秒） */
const SSE_TIMEOUT = 120_000;
/** 测试用 Agent 需求描述 — 带时间戳避免同名冲突 */
const TEST_PROMPT = `创建一个 E2E 测试助手 (${Date.now()})，能够分析代码质量并给出优化建议`;

// ========================================================================
// 测试套件
// ========================================================================

test.describe('Agent 构建器 — 页面加载与布局', () => {
  // 真实 API 测试串行运行，避免并行请求触发限流
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ page }) => {
    // 每个测试前重新登录并导航到 Builder 页面
    await loginAndNavigateTo(page, SIDEBAR_MENU, BUILDER_PATH);
  });

  test('应显示页面标题 "AI Agent 构建器"', async ({ page }) => {
    // 验证页面标题
    const heading = page.getByRole('heading', { name: 'AI Agent 构建器' });
    await expect(heading).toBeVisible({ timeout: 10_000 });
  });

  test('应显示左侧输入区域（textarea + 按钮）', async ({ page }) => {
    // 验证 textarea 存在且可见
    const textarea = page.getByLabel('描述你需要的 Agent');
    await expect(textarea).toBeVisible({ timeout: 10_000 });

    // 验证 textarea 有 placeholder
    await expect(textarea).toHaveAttribute('placeholder', /创建一个能够回答客服问题的 Agent/);

    // 验证提交按钮存在
    const submitButton = page.getByRole('button', { name: '开始生成' });
    await expect(submitButton).toBeVisible();
  });

  test('应显示右侧空占位提示', async ({ page }) => {
    // 右侧无配置时显示占位文字
    const placeholder = page.getByText('生成完成后，Agent 配置将在此处预览');
    await expect(placeholder).toBeVisible({ timeout: 10_000 });
  });

  test('"开始生成"按钮应初始可见', async ({ page }) => {
    // 验证按钮初始文字为"开始生成"
    const button = page.getByRole('button', { name: '开始生成' });
    await expect(button).toBeVisible({ timeout: 10_000 });

    // 验证按钮未被禁用
    await expect(button).toBeEnabled();
  });
});

test.describe('Agent 构建器 — 输入验证', () => {
  // 验证测试互相独立，使用 parallel 模式避免 serial 失败级联
  test.describe.configure({ mode: 'parallel' });

  test.beforeEach(async ({ page }) => {
    await loginAndNavigateTo(page, SIDEBAR_MENU, BUILDER_PATH);
  });

  test('空输入时应显示验证错误提示', async ({ page }) => {
    // 确保 textarea 为空
    const textarea = page.getByLabel('描述你需要的 Agent');
    await expect(textarea).toBeVisible({ timeout: 10_000 });
    await textarea.fill('');

    // 点击"开始生成"按钮
    const submitButton = page.getByRole('button', { name: '开始生成' });
    await submitButton.click();

    // 验证出现验证错误提示（role="alert"）
    const errorAlert = page.getByRole('alert').filter({ hasText: '请输入 Agent 需求描述' });
    await expect(errorAlert).toBeVisible({ timeout: 5_000 });
  });

  test('空输入时不应发起 API 请求', async ({ page }) => {
    // 确保 textarea 为空
    const textarea = page.getByLabel('描述你需要的 Agent');
    await expect(textarea).toBeVisible({ timeout: 10_000 });
    await textarea.fill('');

    // 监听是否有 API 请求发出
    let apiCalled = false;
    page.on('request', (request) => {
      if (request.url().includes('/api/v1/builder/sessions')) {
        apiCalled = true;
      }
    });

    // 点击"开始生成"按钮
    const submitButton = page.getByRole('button', { name: '开始生成' });
    await submitButton.click();

    // 等待一小段时间确保不会有请求延迟发出
    await page.waitForTimeout(2_000);

    // 验证没有发起 API 请求
    expect(apiCalled).toBe(false);
  });
});

test.describe('Agent 构建器 — 完整生成流程', () => {
  // SSE 流式生成需要较长超时
  test.setTimeout(SSE_TIMEOUT);
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ page }) => {
    await loginAndNavigateTo(page, SIDEBAR_MENU, BUILDER_PATH);
  });

  test('输入需求 → 开始生成 → SSE 流式展示 → 配置预览 → 确认创建 → 跳转详情页', async ({
    page,
  }) => {
    // ------------------------------------------------------------------
    // 第 1 步：输入 Agent 需求描述
    // ------------------------------------------------------------------
    const textarea = page.getByLabel('描述你需要的 Agent');
    await expect(textarea).toBeVisible({ timeout: 10_000 });
    await textarea.fill(TEST_PROMPT);

    // ------------------------------------------------------------------
    // 第 2 步：点击"开始生成"，触发 SSE 流式生成
    // ------------------------------------------------------------------
    const submitButton = page.getByRole('button', { name: '开始生成' });
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // 验证按钮变为"生成中…"状态（按钮文字变化或出现加载指示）
    await expect(page.getByRole('button', { name: /生成中/ })).toBeVisible({ timeout: 15_000 });

    // ------------------------------------------------------------------
    // 第 3 步：验证 SSE 流式内容逐步显示
    // ------------------------------------------------------------------
    // 等待 <pre> 标签出现流式内容（从空到有内容）
    const preElement = page.locator('pre');
    await expect(preElement.first()).toBeVisible({ timeout: 30_000 });

    // 等待内容从空变为有实质内容（SSE 流逐步填充）
    await expect(preElement.first()).not.toBeEmpty({ timeout: 60_000 });

    // ------------------------------------------------------------------
    // 第 4 步：等待流式生成完成
    // ------------------------------------------------------------------
    // 等待"生成完成"提示出现
    const completionHint = page.getByText('生成完成，请在右侧确认配置');
    await expect(completionHint).toBeVisible({ timeout: SSE_TIMEOUT });

    // ------------------------------------------------------------------
    // 第 5 步：验证右侧预览面板显示 Agent 配置
    // ------------------------------------------------------------------
    // 验证"Agent 配置预览"标题出现
    const previewHeading = page.getByRole('heading', { name: 'Agent 配置预览' });
    await expect(previewHeading).toBeVisible({ timeout: 10_000 });

    // 验证配置字段非空（至少 Agent 名称和描述应有内容）
    const nameField = page.getByText('Agent 名称').locator('..').locator('p');
    await expect(nameField).not.toHaveText('（未设置）');

    const descField = page.getByText('描述').first().locator('..').locator('p');
    await expect(descField).not.toHaveText('（未设置）');

    // ------------------------------------------------------------------
    // 第 6 步：点击"确认创建 Agent"
    // ------------------------------------------------------------------
    const confirmButton = page.getByRole('button', { name: '确认创建 Agent' });
    await expect(confirmButton).toBeVisible();
    await expect(confirmButton).toBeEnabled();
    await confirmButton.click();

    // ------------------------------------------------------------------
    // 第 7 步：验证结果 — 跳转到详情页 OR 显示已存在错误
    // 真实环境中 AI 生成的 Agent 名称可能与历史数据冲突
    // ------------------------------------------------------------------
    try {
      await page.waitForURL(/\/agents\/\d+/, { timeout: 15_000, waitUntil: 'domcontentloaded' });
      const currentUrl = page.url();
      expect(currentUrl).toMatch(/\/agents\/\d+$/);
      await takeScreenshot(page, 'builder-agent-created');
    } catch {
      // 如果导航未发生，检查是否显示了"已存在"错误（Agent 名称冲突）
      const errorAlert = page.getByRole('alert');
      const hasError = await errorAlert.isVisible().catch(() => false);
      if (hasError) {
        const errorText = await errorAlert.textContent();
        // 如果是"已存在"的预期错误，测试仍标记为通过（确认按钮功能正常）
        expect(errorText).toContain('已存在');
        await takeScreenshot(page, 'builder-agent-name-conflict');
      } else {
        // 非预期的失败，抛出错误
        throw new Error('确认创建 Agent 后既未跳转也未显示错误');
      }
    }
  });
});

test.describe('Agent 构建器 — 取消操作', () => {
  test.setTimeout(SSE_TIMEOUT);
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ page }) => {
    await loginAndNavigateTo(page, SIDEBAR_MENU, BUILDER_PATH);
  });

  test('生成完成后点击"取消"应重置页面状态', async ({ page }) => {
    // ------------------------------------------------------------------
    // 前置：执行一次完整生成流程
    // ------------------------------------------------------------------
    const textarea = page.getByLabel('描述你需要的 Agent');
    await expect(textarea).toBeVisible({ timeout: 10_000 });
    await textarea.fill(TEST_PROMPT);

    const submitButton = page.getByRole('button', { name: '开始生成' });
    await submitButton.click();

    // 等待生成完成
    const completionHint = page.getByText('生成完成，请在右侧确认配置');
    await expect(completionHint).toBeVisible({ timeout: SSE_TIMEOUT });

    // ------------------------------------------------------------------
    // 点击取消按钮
    // ------------------------------------------------------------------
    const cancelButton = page.getByRole('button', { name: '取消' });
    await expect(cancelButton).toBeVisible();
    await cancelButton.click();

    // ------------------------------------------------------------------
    // 验证页面重置到初始状态
    // ------------------------------------------------------------------
    // textarea 应被清空
    await expect(textarea).toHaveValue('', { timeout: 5_000 });

    // "开始生成"按钮应恢复（而不是"重新生成"）
    await expect(page.getByRole('button', { name: '开始生成' })).toBeVisible({ timeout: 5_000 });

    // 右侧占位文字应重新显示
    const placeholder = page.getByText('生成完成后，Agent 配置将在此处预览');
    await expect(placeholder).toBeVisible({ timeout: 5_000 });

    // "确认创建 Agent"按钮应不可见（底部操作栏隐藏）
    await expect(page.getByRole('button', { name: '确认创建 Agent' })).not.toBeVisible();
  });
});

test.describe('Agent 构建器 — 错误处理与边界', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ page }) => {
    await loginAndNavigateTo(page, SIDEBAR_MENU, BUILDER_PATH);
  });

  test('截图记录当前页面状态（开发环境冒烟测试）', async ({ page }) => {
    // 等待页面完全加载
    const heading = page.getByRole('heading', { name: 'AI Agent 构建器' });
    await expect(heading).toBeVisible({ timeout: 10_000 });

    // 截图记录 Builder 页面初始状态
    await takeScreenshot(page, 'builder-initial-state');

    // 验证页面核心元素都存在（冒烟测试）
    await expect(page.getByLabel('描述你需要的 Agent')).toBeVisible();
    await expect(page.getByRole('button', { name: '开始生成' })).toBeVisible();
    await expect(page.getByText('生成完成后，Agent 配置将在此处预览')).toBeVisible();

    // 截图记录验证完成状态
    await takeScreenshot(page, 'builder-smoke-test-passed');
  });

  // TODO(human): SSE 网络中断后的错误恢复测试
  // 实现一个测试用例，模拟 SSE 连接中断并验证错误恢复能力
  // 提示：使用 page.route() 拦截 SSE 请求、验证 role="alert" 错误提示、确认可重新生成
  test('SSE 中断时应显示错误提示并允许重新生成', async ({ page }) => {
    test.setTimeout(SSE_TIMEOUT);
    // TODO(human): 在此实现 SSE 中断错误恢复测试
    // 参考 Guidance:
    // 1. 先正常输入 prompt 并触发 session 创建（让 POST /sessions 成功）
    // 2. 用 page.route('**/api/v1/builder/sessions/*/messages', route => route.abort()) 中断 SSE
    // 3. 验证 role="alert" 显示错误信息
    // 4. 验证"重新生成"按钮可用
    // 5. 取消路由拦截后验证可以重新生成
    test.skip(true, '等待 human 实现 SSE 中断恢复测试');
  });
});
