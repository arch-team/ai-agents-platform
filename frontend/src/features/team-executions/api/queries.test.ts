import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import type { TeamExecution } from './types';
import { useTeamExecutions, useTeamExecution, useTeamExecutionLogs } from './queries';

const API_BASE = 'http://localhost:8000';

const mockExecution: TeamExecution = {
  id: 1,
  agent_id: 1,
  user_id: 1,
  prompt: '测试执行',
  status: 'completed',
  result: '执行完成',
  error: null,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T01:00:00Z',
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('team-executions API hooks', () => {
  beforeEach(() => {
    server.use(
      http.get(`${API_BASE}/api/v1/team-executions`, () =>
        HttpResponse.json({
          items: [mockExecution],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1,
        }),
      ),
      http.get(`${API_BASE}/api/v1/team-executions/:id`, () =>
        HttpResponse.json(mockExecution),
      ),
      http.get(`${API_BASE}/api/v1/team-executions/:id/logs`, () =>
        HttpResponse.json([
          {
            id: 1,
            execution_id: 1,
            sequence: 1,
            agent_name: 'Agent-1',
            content: '开始执行任务',
            created_at: '2025-01-01T00:00:00Z',
          },
        ]),
      ),
    );
  });

  describe('useTeamExecutions', () => {
    it('应成功获取执行列表', async () => {
      const { result } = renderHook(() => useTeamExecutions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].prompt).toBe('测试执行');
    });

    it('应处理请求失败', async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/team-executions`, () =>
          HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
        ),
      );

      const { result } = renderHook(() => useTeamExecutions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useTeamExecution', () => {
    it('应成功获取执行详情', async () => {
      const { result } = renderHook(() => useTeamExecution(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.prompt).toBe('测试执行');
      expect(result.current.data?.status).toBe('completed');
    });

    it('id 为 null 时不应发起请求', () => {
      const { result } = renderHook(() => useTeamExecution(null), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });

  describe('useTeamExecutionLogs', () => {
    it('应成功获取执行日志', async () => {
      const { result } = renderHook(() => useTeamExecutionLogs(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].agent_name).toBe('Agent-1');
    });

    it('id 为 null 时不应发起请求', () => {
      const { result } = renderHook(() => useTeamExecutionLogs(null), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });
});
