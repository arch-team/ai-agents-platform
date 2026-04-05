// builder API hooks 单元测试
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import { useGetBuilderSession } from './queries';
import {
  useCreateBuilderSession,
  useConfirmBuilderSession,
  useConfirmAndTest,
  useStartTesting,
  useGoLive,
  useCancelBuilderSession,
} from './mutations';

import type { BuilderSession } from './types';

const API_BASE = 'http://localhost:8000';

const mockSession: BuilderSession = {
  id: 1,
  user_id: 1,
  prompt: '创建一个客服助手',
  status: 'confirmed',
  generated_config: {
    name: '客服助手',
    description: '智能客服 Agent',
    system_prompt: '你是一个客服助手',
    model_id: 'claude-3-5-sonnet',
    temperature: 0.7,
    max_tokens: 4096,
  },
  agent_name: '客服助手',
  created_agent_id: 1,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('builder API hooks', () => {
  describe('useGetBuilderSession', () => {
    it('应成功获取 Builder 会话详情', async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/builder/sessions/:id`, () => HttpResponse.json(mockSession)),
      );

      const { result } = renderHook(() => useGetBuilderSession(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.prompt).toBe('创建一个客服助手');
      expect(result.current.data?.status).toBe('confirmed');
      expect(result.current.data?.generated_config?.name).toBe('客服助手');
    });

    it('sessionId 为 null 时不应发起请求', () => {
      const { result } = renderHook(() => useGetBuilderSession(null), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });

    it('API 错误时应返回错误状态', async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/builder/sessions/:id`, () =>
          HttpResponse.json({ message: '会话不存在' }, { status: 404 }),
        ),
      );

      const { result } = renderHook(() => useGetBuilderSession(999), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useCreateBuilderSession', () => {
    it('应成功创建 Builder 会话', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/builder/sessions`, () =>
          HttpResponse.json(mockSession, { status: 201 }),
        ),
      );

      const { result } = renderHook(() => useCreateBuilderSession(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.mutateAsync({ prompt: '创建客服 Agent' });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.id).toBe(1);
    });
  });

  describe('useConfirmBuilderSession', () => {
    it('应成功确认会话', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/builder/sessions/:id/confirm`, () =>
          HttpResponse.json({ ...mockSession, created_agent_id: 42 }),
        ),
      );

      const { result } = renderHook(() => useConfirmBuilderSession(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.mutateAsync({ sessionId: 1, nameOverride: '客服助手' });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useConfirmAndTest', () => {
    it('应成功确认并启动测试', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/builder/sessions/:id/confirm`, () =>
          HttpResponse.json({ ...mockSession, created_agent_id: 42 }),
        ),
      );

      const { result } = renderHook(() => useConfirmAndTest(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.mutateAsync({ sessionId: 1, auto_start_testing: true });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useStartTesting', () => {
    it('应成功触发开始测试', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/agents/:id/start-testing`, () =>
          HttpResponse.json({ id: 1, name: '客服助手', status: 'testing' }),
        ),
      );

      const { result } = renderHook(() => useStartTesting(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.mutateAsync(1);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useGoLive', () => {
    it('应成功触发上线', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/agents/:id/go-live`, () =>
          HttpResponse.json({ id: 1, name: '客服助手', status: 'active' }),
        ),
      );

      const { result } = renderHook(() => useGoLive(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.mutateAsync(1);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useCancelBuilderSession', () => {
    it('应成功取消会话', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/builder/sessions/:id/cancel`, () =>
          HttpResponse.json({ ...mockSession, status: 'cancelled' }),
        ),
      );

      const { result } = renderHook(() => useCancelBuilderSession(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.mutateAsync(1);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });
});
