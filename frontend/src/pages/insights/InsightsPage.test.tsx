// Insights 仪表板页面 smoke test
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { renderWithProviders } from '../../../tests/utils';

// Mock feature 组件，避免 API 调用
vi.mock('@/features/insights', () => ({
  InsightsSummary: () => <section aria-label="概览统计">概览统计</section>,
  CostBreakdownChart: () => <section aria-label="成本分布">成本分布</section>,
  UsageTrendChart: () => <section aria-label="使用趋势">使用趋势</section>,
  DateRangePicker: () => (
    <div role="group" aria-label="日期选择器">
      日期选择器
    </div>
  ),
}));

import InsightsPage from './index';

describe('InsightsPage', () => {
  it('should render page title', () => {
    renderWithProviders(<InsightsPage />);
    expect(screen.getByRole('heading', { level: 1, name: 'Insights 仪表板' })).toBeInTheDocument();
  });

  it('should render insights components', () => {
    renderWithProviders(<InsightsPage />);
    expect(screen.getByRole('region', { name: '概览统计' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: '成本分布' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: '使用趋势' })).toBeInTheDocument();
    expect(screen.getByRole('group', { name: '日期选择器' })).toBeInTheDocument();
  });
});
