import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { PageResponse } from '@/shared/types';

import { server } from '../../../../tests/mocks/server';

import type { Tool } from '../api/types';

import { ToolList } from './ToolList';

const API_BASE = 'http://localhost:8000';

// 测试数据
const mockTools: Tool[] = [
  {
    id: 'tool-1',
    name: '代码搜索工具',
    description: '基于语义的代码搜索工具',
    tool_type: 'mcp_server',
    status: 'approved',
    version: '1.0.0',
    configuration: {},
    created_by: 'admin',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    approved_by: 'reviewer',
    approved_at: '2025-01-01T12:00:00Z',
  },
  {
    id: 'tool-2',
    name: 'API 网关',
    description: '统一 API 调用网关',
    tool_type: 'api',
    status: 'draft',
    version: '0.1.0',
    configuration: {},
    created_by: 'dev',
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

const mockResponse: PageResponse<Tool> = {
  items: mockTools,
  total: 2,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('ToolList', () => {
  beforeEach(() => {
    server.use(http.get(`${API_BASE}/api/v1/tools`, () => HttpResponse.json(mockResponse)));
  });

  it('应显示加载状态', () => {
    render(<ToolList />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示工具列表', async () => {
    render(<ToolList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('代码搜索工具')).toBeInTheDocument();
    });
    expect(screen.getByText('API 网关')).toBeInTheDocument();
    expect(screen.getByText('基于语义的代码搜索工具')).toBeInTheDocument();
    expect(screen.getByText('统一 API 调用网关')).toBeInTheDocument();
  });

  it('应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/tools`, () =>
        HttpResponse.json({
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
          total_pages: 0,
        }),
      ),
    );

    render(<ToolList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('暂无工具')).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/tools`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<ToolList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('点击工具卡片应调用 onSelect', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();

    render(<ToolList onSelect={handleSelect} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('代码搜索工具')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /查看工具 代码搜索工具 的详情/ }));
    expect(handleSelect).toHaveBeenCalledWith('tool-1');
  });

  it('应显示注册工具按钮', async () => {
    render(<ToolList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('代码搜索工具')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '注册工具' })).toBeInTheDocument();
  });

  it('点击注册工具应打开对话框', async () => {
    const user = userEvent.setup();

    render(<ToolList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('代码搜索工具')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: '注册工具' }));

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    expect(screen.getByText('注册新工具')).toBeInTheDocument();
  });

  it('应显示状态筛选下拉', async () => {
    render(<ToolList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('代码搜索工具')).toBeInTheDocument();
    });

    const statusFilter = screen.getByLabelText('状态');
    expect(statusFilter).toBeInTheDocument();
    expect(statusFilter).toHaveValue('');
  });

  it('应显示类型筛选下拉', async () => {
    render(<ToolList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('代码搜索工具')).toBeInTheDocument();
    });

    const typeFilter = screen.getByLabelText('类型');
    expect(typeFilter).toBeInTheDocument();
    expect(typeFilter).toHaveValue('');
  });

  it('应显示版本号', async () => {
    render(<ToolList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('代码搜索工具')).toBeInTheDocument();
    });

    expect(screen.getByText('v1.0.0')).toBeInTheDocument();
  });
});
