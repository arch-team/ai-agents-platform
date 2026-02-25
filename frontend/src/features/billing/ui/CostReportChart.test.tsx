import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CostReportChart } from './CostReportChart';

// Mock recharts 避免 SVG 渲染问题
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="chart">{children}</div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
}));

vi.mock('../api/queries', () => ({
  useCostReport: vi.fn(),
}));

import { useCostReport } from '../api/queries';

const dateRange = { start_date: '2024-01-01', end_date: '2024-01-31' };

describe('CostReportChart', () => {
  it('should render chart with data', () => {
    vi.mocked(useCostReport).mockReturnValue({
      data: {
        department_id: 1,
        department_code: 'engineering',
        department_name: '工程部',
        total_cost: 123.45,
        budget_amount: 10000,
        used_percentage: 1.23,
        daily_costs: [
          { date: '2024-01-01', department_code: 'engineering', amount: 60, currency: 'USD' },
          { date: '2024-01-02', department_code: 'engineering', amount: 63.45, currency: 'USD' },
        ],
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        currency: 'USD',
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useCostReport>);

    render(<CostReportChart departmentId={1} dateRange={dateRange} />);

    expect(screen.getByText('成本趋势')).toBeInTheDocument();
    expect(screen.getByText('$123.45')).toBeInTheDocument();
    expect(screen.getByText('$10,000')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    vi.mocked(useCostReport).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as ReturnType<typeof useCostReport>);

    render(<CostReportChart departmentId={1} dateRange={dateRange} />);

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('should show empty state when no data', () => {
    vi.mocked(useCostReport).mockReturnValue({
      data: {
        department_id: 1,
        department_code: 'engineering',
        department_name: '工程部',
        total_cost: 0,
        budget_amount: 10000,
        used_percentage: 0,
        daily_costs: [],
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        currency: 'USD',
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useCostReport>);

    render(<CostReportChart departmentId={1} dateRange={dateRange} />);

    expect(screen.getByText(/暂无成本数据/)).toBeInTheDocument();
  });
});
