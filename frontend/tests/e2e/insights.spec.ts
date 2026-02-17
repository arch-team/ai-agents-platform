import { test, expect } from '@playwright/test';

import { mockAll } from './helpers/api-mock';
import { LOGIN_CREDENTIALS } from './fixtures/mock-data';

test.describe('使用洞察', () => {
  test.beforeEach(async ({ page }) => {
    await mockAll(page);
    await page.goto('/login');
    await page.getByLabel('邮箱').fill(LOGIN_CREDENTIALS.email);
    await page.getByLabel('密码').fill(LOGIN_CREDENTIALS.password);
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/');
  });

  test('Insights 页面应显示正确标题', async ({ page }) => {
    await page.getByLabel('主导航').getByText('使用洞察').click();
    await expect(page).toHaveURL('/insights');

    await expect(page.getByRole('heading', { name: 'Insights 仪表板' })).toBeVisible();
  });

  test('应显示时间范围选择器', async ({ page }) => {
    await page.getByLabel('主导航').getByText('使用洞察').click();
    await expect(page).toHaveURL('/insights');

    // 验证预设时间按钮
    await expect(page.getByRole('button', { name: '最近 7 天' })).toBeVisible();
    await expect(page.getByRole('button', { name: '最近 30 天' })).toBeVisible();
  });

  test('应显示概览统计卡片', async ({ page }) => {
    await page.getByLabel('主导航').getByText('使用洞察').click();
    await expect(page).toHaveURL('/insights');

    // 等待概览统计加载完成（等待第一个统计值出现）
    await expect(page.getByText('Agent 总数')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/活跃 Agent/)).toBeVisible();
    await expect(page.getByText('调用总量')).toBeVisible();
    await expect(page.getByRole('term').filter({ hasText: '总 Token' })).toBeVisible();
    await expect(page.getByText('平台总成本')).toBeVisible();
  });

  test('应显示使用趋势图区域', async ({ page }) => {
    await page.getByLabel('主导航').getByText('使用洞察').click();
    await expect(page).toHaveURL('/insights');

    await expect(page.getByText('使用趋势')).toBeVisible();
  });

  test('应显示 Token 归因表格', async ({ page }) => {
    await page.getByLabel('主导航').getByText('使用洞察').click();
    await expect(page).toHaveURL('/insights');

    await expect(page.getByText(/Token 消耗归因/)).toBeVisible();

    // 验证表格中的 Agent 名称（使用 getByRole 精确定位到表格单元格，避免图表中的同名文本）
    await expect(page.getByRole('cell', { name: '客服助手' })).toBeVisible();
  });
});
