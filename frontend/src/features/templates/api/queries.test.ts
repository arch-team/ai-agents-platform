import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import type { Template, TemplateListResponse } from './types';
import { useTemplates, useTemplate, usePublishedTemplates, useCreateTemplate, useUpdateTemplate, useDeleteTemplate, usePublishTemplate, useArchiveTemplate } from './queries';

const API_BASE = 'http://localhost:8000';

const mockTemplate: Template = {
  id: 1,
  name: '测试模板',
  description: '测试用模板',
  category: 'customer_service',
  status: 'published',
  creator_id: 1,
  system_prompt: '你是助手',
  model_id: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
  temperature: 0.7,
  max_tokens: 4096,
  tool_ids: [],
  knowledge_base_ids: [],
  tags: [],
  usage_count: 10,
  is_featured: false,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

const mockListResponse: TemplateListResponse = {
  items: [mockTemplate],
  total: 1,
  page: 1,
  page_size: 12,
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

describe('templates API hooks', () => {
  beforeEach(() => {
    server.use(
      http.get(`${API_BASE}/api/v1/templates`, () => HttpResponse.json(mockListResponse)),
      http.get(`${API_BASE}/api/v1/templates/published`, () => HttpResponse.json(mockListResponse)),
      http.get(`${API_BASE}/api/v1/templates/:id`, () => HttpResponse.json(mockTemplate)),
    );
  });

  describe('useTemplates', () => {
    it('应成功获取模板列表', async () => {
      const { result } = renderHook(() => useTemplates(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].name).toBe('测试模板');
    });

    it('应处理请求失败', async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/templates`, () =>
          HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
        ),
      );

      const { result } = renderHook(() => useTemplates(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('usePublishedTemplates', () => {
    it('应成功获取已发布模板列表', async () => {
      const { result } = renderHook(() => usePublishedTemplates(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(1);
    });
  });

  describe('useTemplate', () => {
    it('应成功获取模板详情', async () => {
      const { result } = renderHook(() => useTemplate(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.name).toBe('测试模板');
      expect(result.current.data?.category).toBe('customer_service');
    });

    it('id 为 undefined 时不应发起请求', () => {
      const { result } = renderHook(() => useTemplate(undefined), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });

  describe('useCreateTemplate', () => {
    it('应成功创建模板', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/templates`, () => HttpResponse.json(mockTemplate)),
      );

      const { result } = renderHook(() => useCreateTemplate(), {
        wrapper: createWrapper(),
      });

      const newTemplate = await result.current.mutateAsync({
        name: '新模板',
        description: '测试创建',
        category: 'customer_service',
        system_prompt: '你是助手',
      });

      expect(newTemplate.name).toBe('测试模板');
    });
  });

  describe('useUpdateTemplate', () => {
    it('应成功更新模板', async () => {
      const updatedTemplate = { ...mockTemplate, name: '更新后的模板' };
      server.use(
        http.put(`${API_BASE}/api/v1/templates/:id`, () => HttpResponse.json(updatedTemplate)),
      );

      const { result } = renderHook(() => useUpdateTemplate(), {
        wrapper: createWrapper(),
      });

      const updated = await result.current.mutateAsync({
        id: 1,
        name: '更新后的模板',
      });

      expect(updated.name).toBe('更新后的模板');
    });
  });

  describe('useDeleteTemplate', () => {
    it('应成功删除模板', async () => {
      server.use(
        http.delete(`${API_BASE}/api/v1/templates/:id`, () => new HttpResponse(null, { status: 204 })),
      );

      const { result } = renderHook(() => useDeleteTemplate(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.mutateAsync(1)).resolves.toBeUndefined();
    });
  });

  describe('usePublishTemplate', () => {
    it('应成功发布模板', async () => {
      const publishedTemplate = { ...mockTemplate, status: 'published' as const };
      server.use(
        http.post(`${API_BASE}/api/v1/templates/:id/publish`, () => HttpResponse.json(publishedTemplate)),
      );

      const { result } = renderHook(() => usePublishTemplate(), {
        wrapper: createWrapper(),
      });

      const published = await result.current.mutateAsync(1);

      expect(published.status).toBe('published');
    });
  });

  describe('useArchiveTemplate', () => {
    it('应成功归档模板', async () => {
      const archivedTemplate = { ...mockTemplate, status: 'archived' as const };
      server.use(
        http.post(`${API_BASE}/api/v1/templates/:id/archive`, () => HttpResponse.json(archivedTemplate)),
      );

      const { result } = renderHook(() => useArchiveTemplate(), {
        wrapper: createWrapper(),
      });

      const archived = await result.current.mutateAsync(1);

      expect(archived.status).toBe('archived');
    });
  });
});
