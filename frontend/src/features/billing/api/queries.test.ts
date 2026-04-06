import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import {
  billingKeys,
  useCreateDepartment,
  useUpdateDepartment,
  useDeleteDepartment,
  useCreateBudget,
  useUpdateBudget,
} from './queries';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return {
    queryClient,
    Wrapper: ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children),
  };
}

describe('billingKeys', () => {
  it('should generate department list key', () => {
    const key = billingKeys.departmentList(1, 50);
    expect(key).toEqual(['billing', 'departments', 'list', 1, 50]);
  });

  it('should generate budget list key', () => {
    const key = billingKeys.budgetList(1, 1);
    expect(key).toEqual(['billing', 'budgets', 1, 'list', 1]);
  });

  it('should generate current budget key', () => {
    const key = billingKeys.currentBudget(1, 2024, 3);
    expect(key).toEqual(['billing', 'budgets', 1, 'current', 2024, 3]);
  });

  it('should generate cost report key', () => {
    const params = { start_date: '2024-01-01', end_date: '2024-01-31' };
    const key = billingKeys.costReport(1, params);
    expect(key).toEqual(['billing', 'cost-report', 1, params]);
  });
});

// ── Mutation Tests ──

describe('useCreateDepartment', () => {
  it('应成功创建部门', async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/billing/departments`, async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(
          {
            id: 2,
            ...body,
            is_active: true,
            created_at: '2025-01-02T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
          },
          { status: 201 },
        );
      }),
    );

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useCreateDepartment(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        name: '市场部',
        code: 'MKT',
        description: '市场营销部门',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.id).toBe(2);
    expect(result.current.data?.name).toBe('市场部');
  });

  it('创建失败时应返回错误', async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/billing/departments`, () =>
        HttpResponse.json({ message: '部门代码已存在' }, { status: 400 }),
      ),
    );

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useCreateDepartment(), { wrapper: Wrapper });

    await act(async () => {
      try {
        await result.current.mutateAsync({ name: '市场部', code: 'MKT' });
      } catch {
        // 期望抛出错误
      }
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateDepartment', () => {
  it('应成功更新部门', async () => {
    server.use(
      http.put(`${API_BASE}/api/v1/billing/departments/:id`, async ({ request, params }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          id: Number(params.id),
          name: '研发部',
          code: 'DEV',
          description: '研发部门',
          is_active: true,
          ...body,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-02T00:00:00Z',
        });
      }),
    );

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdateDepartment(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        id: 1,
        name: '研发中心',
        description: '研发中心部门',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.name).toBe('研发中心');
  });
});

describe('useDeleteDepartment', () => {
  it('应成功删除部门', async () => {
    server.use(
      http.delete(`${API_BASE}/api/v1/billing/departments/:id`, () =>
        new HttpResponse(null, { status: 204 }),
      ),
    );

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useDeleteDepartment(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.mutateAsync(1);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCreateBudget', () => {
  it('应成功创建预算', async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/billing/budgets`, async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(
          {
            id: 2,
            ...body,
            used_amount: 0,
            alert_threshold: body.alert_threshold || 0.8,
            created_at: '2025-01-02T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
          },
          { status: 201 },
        );
      }),
    );

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useCreateBudget(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        department_id: 1,
        year: 2025,
        month: 2,
        budget_amount: 15000,
        alert_threshold: 0.9,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.id).toBe(2);
    expect(result.current.data?.budget_amount).toBe(15000);
  });
});

describe('useUpdateBudget', () => {
  it('应成功更新预算', async () => {
    server.use(
      http.put(`${API_BASE}/api/v1/billing/budgets/:id`, async ({ request, params }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          id: Number(params.id),
          department_id: 1,
          year: 2025,
          month: 1,
          budget_amount: 10000,
          used_amount: 3500,
          alert_threshold: 0.8,
          ...body,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-02T00:00:00Z',
        });
      }),
    );

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdateBudget(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        id: 1,
        budget_amount: 20000,
        alert_threshold: 0.85,
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.budget_amount).toBe(20000);
  });
});
