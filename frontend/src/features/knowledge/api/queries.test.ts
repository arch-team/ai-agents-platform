import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import type { KnowledgeBase, KnowledgeBaseListResponse } from './types';
import { useKnowledgeBases, useKnowledgeBase, useKnowledgeDocuments } from './queries';

const API_BASE = 'http://localhost:8000';

const mockKB: KnowledgeBase = {
  id: 1,
  name: '测试知识库',
  description: '测试用知识库',
  status: 'ACTIVE',
  document_count: 5,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

const mockListResponse: KnowledgeBaseListResponse = {
  items: [mockKB],
  total: 1,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('knowledge API hooks', () => {
  beforeEach(() => {
    server.use(
      http.get(`${API_BASE}/api/v1/knowledge-bases`, () =>
        HttpResponse.json(mockListResponse),
      ),
      http.get(`${API_BASE}/api/v1/knowledge-bases/:id`, () =>
        HttpResponse.json(mockKB),
      ),
      http.get(`${API_BASE}/api/v1/knowledge-bases/:id/documents`, () =>
        HttpResponse.json({
          items: [
            {
              id: 1,
              knowledge_base_id: 1,
              file_name: 'test.pdf',
              file_size: 1024,
              content_type: 'application/pdf',
              status: 'processed',
              created_at: '2025-01-01T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 10,
          total_pages: 1,
        }),
      ),
    );
  });

  describe('useKnowledgeBases', () => {
    it('应成功获取知识库列表', async () => {
      const { result } = renderHook(() => useKnowledgeBases(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].name).toBe('测试知识库');
    });

    it('应处理请求失败', async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/knowledge-bases`, () =>
          HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
        ),
      );

      const { result } = renderHook(() => useKnowledgeBases(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useKnowledgeBase', () => {
    it('应成功获取知识库详情', async () => {
      const { result } = renderHook(() => useKnowledgeBase(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.name).toBe('测试知识库');
      expect(result.current.data?.status).toBe('ACTIVE');
    });

    it('id 为 undefined 时不应发起请求', () => {
      const { result } = renderHook(() => useKnowledgeBase(undefined), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });

  describe('useKnowledgeDocuments', () => {
    it('应成功获取知识库文档列表', async () => {
      const { result } = renderHook(() => useKnowledgeDocuments(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].file_name).toBe('test.pdf');
    });

    it('kbId 为 undefined 时不应发起请求', () => {
      const { result } = renderHook(() => useKnowledgeDocuments(undefined), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });
});
