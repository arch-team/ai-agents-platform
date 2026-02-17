import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';

import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import {
  useTestSuites,
  useTestSuite,
  useTestCases,
  useEvaluationRuns,
  useEvaluationRun,
  useEvaluationResults,
  useCreateTestSuite,
  useDeleteTestSuite,
  useCreateEvaluationRun,
} from './queries';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('useTestSuites', () => {
  it('应返回测试集列表', async () => {
    const { result } = renderHook(() => useTestSuites(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.items[0].name).toBe('回归测试集');
  });

  it('API 错误时应返回错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/test-suites`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    const { result } = renderHook(() => useTestSuites(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useTestSuite', () => {
  it('应返回测试集详情', async () => {
    const { result } = renderHook(() => useTestSuite(1), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.name).toBe('回归测试集');
    expect(result.current.data?.status).toBe('draft');
  });

  it('id 为 undefined 时不应发起请求', () => {
    const { result } = renderHook(() => useTestSuite(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useTestCases', () => {
  it('应返回测试用例列表', async () => {
    const { result } = renderHook(() => useTestCases(1), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0].input_prompt).toBe('你好，请自我介绍');
  });

  it('suiteId 为 undefined 时不应发起请求', () => {
    const { result } = renderHook(() => useTestCases(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useEvaluationRuns', () => {
  it('应返回评估运行列表', async () => {
    const { result } = renderHook(() => useEvaluationRuns(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0].status).toBe('completed');
    expect(result.current.data?.items[0].score).toBe(0.85);
  });
});

describe('useEvaluationRun', () => {
  it('应返回评估运行详情', async () => {
    const { result } = renderHook(() => useEvaluationRun(1), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.passed_cases).toBe(8);
    expect(result.current.data?.failed_cases).toBe(2);
  });

  it('id 为 undefined 时不应发起请求', () => {
    const { result } = renderHook(() => useEvaluationRun(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useEvaluationResults', () => {
  it('应返回评估结果列表', async () => {
    const { result } = renderHook(() => useEvaluationResults(1), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.items[0].passed).toBe(true);
    expect(result.current.data?.items[1].passed).toBe(false);
  });

  it('runId 为 undefined 时不应发起请求', () => {
    const { result } = renderHook(() => useEvaluationResults(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateTestSuite', () => {
  it('应创建测试集并返回新数据', async () => {
    const { result } = renderHook(() => useCreateTestSuite(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ name: '新测试集', agent_id: 1 });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.id).toBe(3);
    expect(result.current.data?.status).toBe('draft');
  });
});

describe('useDeleteTestSuite', () => {
  it('应成功删除测试集', async () => {
    const { result } = renderHook(() => useDeleteTestSuite(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(1);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });
});

describe('useCreateEvaluationRun', () => {
  it('应创建评估运行', async () => {
    const { result } = renderHook(() => useCreateEvaluationRun(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ suite_id: 1 });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.status).toBe('pending');
  });
});
