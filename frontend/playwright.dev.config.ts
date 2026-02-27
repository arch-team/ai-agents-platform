/**
 * Playwright 配置 — Dev 真实环境 E2E 测试
 *
 * 用法: npx playwright test --config=playwright.dev.config.ts
 */
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  // 只运行 real-*.spec.ts 文件（真实环境测试）
  testMatch: 'real-*.spec.ts',
  fullyParallel: false, // 真实环境测试串行执行，避免并发冲突
  retries: 1, // 真实环境允许 1 次重试（网络波动）
  workers: 1, // 单 worker 避免登录状态冲突
  timeout: 60_000, // 60 秒超时（SSE 流式响应需要更长时间）
  expect: {
    timeout: 15_000, // 断言超时 15 秒
  },
  reporter: [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['list'], // 终端输出
  ],
  use: {
    baseURL: 'https://d2k7ovgb2e4af9.cloudfront.net',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    // 真实环境需要更长的导航超时
    navigationTimeout: 20_000,
    actionTimeout: 10_000,
  },
  projects: [
    {
      name: 'chromium-dev',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // 截图输出目录
  outputDir: 'test-results/artifacts',
});
