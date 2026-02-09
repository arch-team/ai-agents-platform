import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { renderWithProviders } from '../../../tests/utils';

import DashboardPage from './index';

describe('DashboardPage', () => {
  it('should render welcome message', () => {
    renderWithProviders(<DashboardPage />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('欢迎回来');
  });

  it('should render quick action links', () => {
    renderWithProviders(<DashboardPage />);
    expect(screen.getByText('创建 Agent')).toBeInTheDocument();
    expect(screen.getByText('查看 Agent 列表')).toBeInTheDocument();
  });

  it('should display statistics', async () => {
    renderWithProviders(<DashboardPage />);
    expect(screen.getByText('Agent 总数')).toBeInTheDocument();
    expect(screen.getByText('对话总数')).toBeInTheDocument();

    // 等待数据加载完成 — 两个统计卡片都显示数字
    await waitFor(() => {
      const statValues = screen.getAllByText('1');
      expect(statValues.length).toBeGreaterThanOrEqual(2);
    });
  });
});
