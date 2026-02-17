import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { InsightsSummary } from './InsightsSummary';

const API_BASE = 'http://localhost:8000';

const defaultDateRange = { start_date: '2025-01-01', end_date: '2025-01-31' };

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('InsightsSummary', () => {
  it('应显示加载状态', () => {
    render(<InsightsSummary dateRange={defaultDateRange} />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示概览统计指标', async () => {
    render(<InsightsSummary dateRange={defaultDateRange} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Agent 总数')).toBeInTheDocument();
    });

    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('活跃 Agent')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('调用总量')).toBeInTheDocument();
    expect(screen.getByText('12.5K')).toBeInTheDocument();
    expect(screen.getByText('总 Token')).toBeInTheDocument();
    expect(screen.getByText('2.5M')).toBeInTheDocument();
    expect(screen.getByText('平台总成本')).toBeInTheDocument();
    expect(screen.getByText('$125.50')).toBeInTheDocument();
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/insights/summary`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<InsightsSummary dateRange={defaultDateRange} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
