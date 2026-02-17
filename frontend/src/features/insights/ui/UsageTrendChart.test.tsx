import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeAll } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { UsageTrendChart } from './UsageTrendChart';

const API_BASE = 'http://localhost:8000';

const defaultDateRange = { start_date: '2025-01-01', end_date: '2025-01-31' };

// recharts 的 ResponsiveContainer 在 jsdom 中依赖 ResizeObserver
beforeAll(() => {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('UsageTrendChart', () => {
  it('应显示加载状态', () => {
    render(<UsageTrendChart dateRange={defaultDateRange} />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示使用趋势标题', async () => {
    render(<UsageTrendChart dateRange={defaultDateRange} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('使用趋势')).toBeInTheDocument();
    });
  });

  it('数据为空时应显示暂无数据', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/insights/usage-trends`, () =>
        HttpResponse.json({
          data_points: [],
          period: { start_date: '2025-01-01', end_date: '2025-01-31' },
        }),
      ),
    );

    render(<UsageTrendChart dateRange={defaultDateRange} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('暂无数据')).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/insights/usage-trends`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<UsageTrendChart dateRange={defaultDateRange} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
