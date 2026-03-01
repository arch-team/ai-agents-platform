// builder API hooks 单元测试
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import { useGetBuilderSession } from './queries';

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
});
