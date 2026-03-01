// execution API hooks 单元测试
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import {
  useConversations,
  useConversation,
  useCreateConversation,
  useCompleteConversation,
} from './queries';

const API_BASE = 'http://localhost:8000';

const mockConversation = {
  id: 1,
  title: '测试对话',
  agent_id: 1,
  user_id: 1,
  status: 'active',
  message_count: 3,
  total_tokens: 100,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

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

describe('execution API hooks', () => {
  describe('useConversations', () => {
    it('应成功获取对话列表', async () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useConversations(), {
        wrapper: Wrapper,
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].title).toBe('测试对话');
    });

    it('传入 agentId 时应作为参数发送', async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/conversations`, ({ request }) => {
          const url = new URL(request.url);
          const agentId = url.searchParams.get('agent_id');
          if (agentId === '1') {
            return HttpResponse.json({
              items: [mockConversation],
              total: 1,
              page: 1,
              page_size: 10,
              total_pages: 1,
            });
          }
          return HttpResponse.json({
            items: [],
            total: 0,
            page: 1,
            page_size: 10,
            total_pages: 0,
          });
        }),
      );

      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useConversations(1), {
        wrapper: Wrapper,
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(1);
    });

    it('API 错误时应返回错误状态', async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/conversations`, () =>
          HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
        ),
      );

      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useConversations(), {
        wrapper: Wrapper,
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useConversation', () => {
    it('应成功获取对话详情', async () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useConversation(1), {
        wrapper: Wrapper,
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.conversation.title).toBe('测试对话');
      expect(result.current.data?.messages).toHaveLength(2);
    });

    it('id 为 null 时不应发起请求', () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useConversation(null), {
        wrapper: Wrapper,
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });

  describe('useCreateConversation', () => {
    it('应成功创建对话', async () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useCreateConversation(), {
        wrapper: Wrapper,
      });

      await act(async () => {
        result.current.mutate({ agent_id: 1, title: '新对话' });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.id).toBeDefined();
    });

    it('创建失败时应返回错误', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/conversations`, () =>
          HttpResponse.json({ message: '创建失败' }, { status: 400 }),
        ),
      );

      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useCreateConversation(), {
        wrapper: Wrapper,
      });

      await act(async () => {
        result.current.mutate({ agent_id: 999 });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useCompleteConversation', () => {
    beforeEach(() => {
      server.use(
        http.post(`${API_BASE}/api/v1/conversations/:id/complete`, ({ params }) =>
          HttpResponse.json({
            ...mockConversation,
            id: Number(params.id),
            status: 'completed',
          }),
        ),
      );
    });

    it('应成功结束对话', async () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useCompleteConversation(), {
        wrapper: Wrapper,
      });

      await act(async () => {
        result.current.mutate(1);
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.status).toBe('completed');
    });

    it('结束失败时应返回错误', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/conversations/:id/complete`, () =>
          HttpResponse.json({ message: '操作失败' }, { status: 400 }),
        ),
      );

      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useCompleteConversation(), {
        wrapper: Wrapper,
      });

      await act(async () => {
        result.current.mutate(1);
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });
});
