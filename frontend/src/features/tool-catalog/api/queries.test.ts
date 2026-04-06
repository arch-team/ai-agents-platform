import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import type { Tool, ToolListResponse } from './types';
import { useTools, useTool, useApprovedTools, useCreateTool, useUpdateTool, useDeleteTool, useSubmitTool, useApproveTool, useRejectTool, useDeprecateTool } from './queries';

const API_BASE = 'http://localhost:8000';

const mockTool: Tool = {
  id: 'tool-1',
  name: '测试工具',
  description: '一个测试用的工具',
  tool_type: 'mcp_server',
  status: 'approved',
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
      http.get(`${API_BASE}/api/v1/tools`, () => HttpResponse.json(mockListResponse)),
      http.get(`${API_BASE}/api/v1/tools/approved`, () => HttpResponse.json(mockListResponse)),
      http.get(`${API_BASE}/api/v1/tools/:id`, () => HttpResponse.json(mockTool)),
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
      expect(result.current.data?.tool_type).toBe('mcp_server');
    });

    it('id 为 undefined 时不应发起请求', () => {
      const { result } = renderHook(() => useTool(undefined), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
    });
  });

  describe('useCreateTool', () => {
    it('应成功创建工具', async () => {
      server.use(
        http.post(`${API_BASE}/api/v1/tools`, () => HttpResponse.json(mockTool)),
      );

      const { result } = renderHook(() => useCreateTool(), {
        wrapper: createWrapper(),
      });

      const newTool = await result.current.mutateAsync({
        name: '新工具',
        description: '测试创建',
        tool_type: 'mcp_server',
      });

      expect(newTool.name).toBe('测试工具');
    });
  });

  describe('useUpdateTool', () => {
    it('应成功更新工具', async () => {
      const updatedTool = { ...mockTool, name: '更新后的工具' };
      server.use(
        http.put(`${API_BASE}/api/v1/tools/:id`, () => HttpResponse.json(updatedTool)),
      );

      const { result } = renderHook(() => useUpdateTool(), {
        wrapper: createWrapper(),
      });

      const updated = await result.current.mutateAsync({
        id: 'tool-1',
        name: '更新后的工具',
      });

      expect(updated.name).toBe('更新后的工具');
    });
  });

  describe('useDeleteTool', () => {
    it('应成功删除工具', async () => {
      server.use(
        http.delete(`${API_BASE}/api/v1/tools/:id`, () => new HttpResponse(null, { status: 204 })),
      );

      const { result } = renderHook(() => useDeleteTool(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.mutateAsync('tool-1')).resolves.toBeUndefined();
    });
  });

  describe('useSubmitTool', () => {
    it('应成功提交审批', async () => {
      const submittedTool = { ...mockTool, status: 'pending_review' as const };
      server.use(
        http.post(`${API_BASE}/api/v1/tools/:id/submit`, () => HttpResponse.json(submittedTool)),
      );

      const { result } = renderHook(() => useSubmitTool(), {
        wrapper: createWrapper(),
      });

      const submitted = await result.current.mutateAsync('tool-1');

      expect(submitted.status).toBe('pending_review');
    });
  });

  describe('useApproveTool', () => {
    it('应成功审批通过工具', async () => {
      const approvedTool = { ...mockTool, status: 'approved' as const };
      server.use(
        http.post(`${API_BASE}/api/v1/tools/:id/approve`, () => HttpResponse.json(approvedTool)),
      );

      const { result } = renderHook(() => useApproveTool(), {
        wrapper: createWrapper(),
      });

      const approved = await result.current.mutateAsync('tool-1');

      expect(approved.status).toBe('approved');
    });
  });

  describe('useRejectTool', () => {
    it('应成功拒绝工具', async () => {
      const rejectedTool = { ...mockTool, status: 'rejected' as const, rejected_reason: '不符合要求' };
      server.use(
        http.post(`${API_BASE}/api/v1/tools/:id/reject`, () => HttpResponse.json(rejectedTool)),
      );

      const { result } = renderHook(() => useRejectTool(), {
        wrapper: createWrapper(),
      });

      const rejected = await result.current.mutateAsync({
        id: 'tool-1',
        reason: '不符合要求',
      });

      expect(rejected.status).toBe('rejected');
      expect(rejected.rejected_reason).toBe('不符合要求');
    });
  });

  describe('useDeprecateTool', () => {
    it('应成功废弃工具', async () => {
      const deprecatedTool = { ...mockTool, status: 'deprecated' as const };
      server.use(
        http.post(`${API_BASE}/api/v1/tools/:id/deprecate`, () => HttpResponse.json(deprecatedTool)),
      );

      const { result } = renderHook(() => useDeprecateTool(), {
        wrapper: createWrapper(),
      });

      const deprecated = await result.current.mutateAsync('tool-1');

      expect(deprecated.status).toBe('deprecated');
    });
  });
});
