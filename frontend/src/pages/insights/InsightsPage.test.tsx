// Insights 仪表板页面 smoke test
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { renderWithProviders } from '../../../tests/utils';

// Mock feature 组件，避免 API 调用
vi.mock('@/features/insights', () => ({
  InsightsSummary: () => <div data-testid="insights-summary">概览统计</div>,
  CostBreakdownChart: () => <div data-testid="cost-breakdown">成本分布</div>,
  UsageTrendChart: () => <div data-testid="usage-trend">使用趋势</div>,
  DateRangePicker: () => <div data-testid="date-range-picker">日期选择器</div>,
}));

import InsightsPage from './index';

describe('InsightsPage', () => {
  it('should render page title', () => {
    renderWithProviders(<InsightsPage />);
    expect(screen.getByRole('heading', { level: 1, name: 'Insights 仪表板' })).toBeInTheDocument();
  });

  it('should render insights components', () => {
    renderWithProviders(<InsightsPage />);
    expect(screen.getByTestId('insights-summary')).toBeInTheDocument();
    expect(screen.getByTestId('cost-breakdown')).toBeInTheDocument();
    expect(screen.getByTestId('usage-trend')).toBeInTheDocument();
    expect(screen.getByTestId('date-range-picker')).toBeInTheDocument();
  });
});
