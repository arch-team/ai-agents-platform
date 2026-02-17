import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';

import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import { useCostBreakdown, useUsageTrends, useInsightsSummary } from './queries';

const API_BASE = 'http://localhost:8000';

const defaultParams = { start_date: '2025-01-01', end_date: '2025-01-31' };

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('useInsightsSummary', () => {
  it('应返回概览统计数据', async () => {
    const { result } = renderHook(() => useInsightsSummary(defaultParams), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.total_agents).toBe(15);
    expect(result.current.data?.active_agents).toBe(8);
    expect(result.current.data?.total_invocations).toBe(12500);
    expect(result.current.data?.total_cost).toBe(125.5);
  });

  it('API 错误时应返回错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/insights/summary`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    const { result } = renderHook(() => useInsightsSummary(defaultParams), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useCostBreakdown', () => {
  it('应返回成本归因数据', async () => {
    const { result } = renderHook(() => useCostBreakdown(defaultParams), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.items[0].agent_name).toBe('客服助手');
    expect(result.current.data?.total_tokens).toBe(800000);
  });

  it('API 错误时应返回错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/insights/cost-breakdown`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    const { result } = renderHook(() => useCostBreakdown(defaultParams), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useUsageTrends', () => {
  it('应返回使用趋势数据', async () => {
    const { result } = renderHook(() => useUsageTrends(defaultParams), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.data_points).toHaveLength(3);
    expect(result.current.data?.data_points[0].invocation_count).toBe(100);
  });

  it('API 错误时应返回错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/insights/usage-trends`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    const { result } = renderHook(() => useUsageTrends(defaultParams), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});
