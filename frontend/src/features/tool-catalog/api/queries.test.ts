import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import type { Tool, ToolListResponse } from './types';
import { useTools, useTool, useApprovedTools } from './queries';

const API_BASE = 'http://localhost:8000';

const mockTool: Tool = {
  id: 'tool-1',
  name: '测试工具',
  description: '一个测试用的工具',
  tool_type: 'MCP_SERVER',
  status: 'APPROVED',
  version: '1.0.0',
  configuration: {},
  created_by: 'admin',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

const mockListResponse: ToolListResponse = {
  items: [mockTool],
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

describe('tool-catalog API hooks', () => {
  beforeEach(() => {
    server.use(
      http.get(`${API_BASE}/api/v1/tools`, () =>
        HttpResponse.json(mockListResponse),
      ),
      http.get(`${API_BASE}/api/v1/tools/approved`, () =>
        HttpResponse.json(mockListResponse),
      ),
      http.get(`${API_BASE}/api/v1/tools/:id`, () =>
        HttpResponse.json(mockTool),
      ),
    );
  });

  describe('useTools', () => {
    it('应成功获取工具列表', async () => {
      const { result } = renderHook(() => useTools(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].name).toBe('测试工具');
    });

    it('应处理请求失败', async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/tools`, () =>
          HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
        ),
      );

      const { result } = renderHook(() => useTools(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useApprovedTools', () => {
    it('应成功获取已审批工具列表', async () => {
      const { result } = renderHook(() => useApprovedTools(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(1);
    });
  });

  describe('useTool', () => {
    it('应成功获取工具详情', async () => {
      const { result } = renderHook(() => useTool('tool-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.name).toBe('测试工具');
      expect(result.current.data?.tool_type).toBe('MCP_SERVER');
    });

    it('id 为 undefined 时不应发起请求', () => {
      const { result } = renderHook(() => useTool(undefined), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });
});
