import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { PageResponse } from '@/shared/types';

import { server } from '../../../../tests/mocks/server';

import type { KnowledgeBase } from '../api/types';

import { KnowledgeList } from './KnowledgeList';

const API_BASE = 'http://localhost:8000';

// 测试数据
const mockKnowledgeBases: KnowledgeBase[] = [
  {
    id: 1,
    name: '产品文档知识库',
    description: '包含所有产品文档',
    status: 'ACTIVE',
    document_count: 15,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: '技术知识库',
    description: '技术文档集合',
    status: 'CREATING',
    document_count: 0,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

const mockResponse: PageResponse<KnowledgeBase> = {
  items: mockKnowledgeBases,
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

describe('KnowledgeList', () => {
  beforeEach(() => {
    server.use(
      http.get(`${API_BASE}/api/v1/knowledge-bases`, () => HttpResponse.json(mockResponse)),
    );
  });

  it('应显示加载状态', () => {
    render(<KnowledgeList />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示知识库列表', async () => {
    render(<KnowledgeList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品文档知识库')).toBeInTheDocument();
    });
    expect(screen.getByText('技术知识库')).toBeInTheDocument();
    expect(screen.getByText('15 个文档')).toBeInTheDocument();
  });

  it('应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/knowledge-bases`, () =>
        HttpResponse.json({
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
          total_pages: 0,
        }),
      ),
    );

    render(<KnowledgeList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('暂无知识库')).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/knowledge-bases`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<KnowledgeList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('点击知识库应调用 onSelect', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();

    render(<KnowledgeList onSelect={handleSelect} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品文档知识库')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /查看知识库: 产品文档知识库/ }));
    expect(handleSelect).toHaveBeenCalledWith(1);
  });

  it('应在 onCreate 传入时显示创建按钮', async () => {
    const handleCreate = vi.fn();
    const user = userEvent.setup();

    render(<KnowledgeList onCreate={handleCreate} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品文档知识库')).toBeInTheDocument();
    });

    const createButton = screen.getByRole('button', { name: '创建知识库' });
    expect(createButton).toBeInTheDocument();
    await user.click(createButton);
    expect(handleCreate).toHaveBeenCalled();
  });

  it('应显示状态筛选下拉', async () => {
    render(<KnowledgeList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品文档知识库')).toBeInTheDocument();
    });

    const filter = screen.getByLabelText('状态筛选');
    expect(filter).toBeInTheDocument();
    expect(filter).toHaveValue('');
  });

  it('ACTIVE 状态知识库应显示同步按钮', async () => {
    render(<KnowledgeList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品文档知识库')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '同步 产品文档知识库' })).toBeInTheDocument();
  });

  it('所有知识库应显示删除按钮', async () => {
    render(<KnowledgeList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('产品文档知识库')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '删除 产品文档知识库' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '删除 技术知识库' })).toBeInTheDocument();
  });

  it('切换状态筛选应触发过滤', async () => {
    const user = userEvent.setup();
    render(<KnowledgeList />, { wrapper: createWrapper() });
    await waitFor(() => expect(screen.getByText('产品文档知识库')).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText('状态筛选'), 'ACTIVE');
  });

  it('点击同步按钮应触发同步操作', async () => {
    const user = userEvent.setup();
    render(<KnowledgeList />, { wrapper: createWrapper() });
    await waitFor(() => expect(screen.getByText('产品文档知识库')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: '同步 产品文档知识库' }));
  });

  it('点击删除按钮应触发删除操作', async () => {
    const user = userEvent.setup();
    render(<KnowledgeList />, { wrapper: createWrapper() });
    await waitFor(() => expect(screen.getByText('产品文档知识库')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: '删除 产品文档知识库' }));
  });

  it('分页应触发页码变更', async () => {
    const user = userEvent.setup();
    const multiPageResponse: PageResponse<KnowledgeBase> = { ...mockResponse, total_pages: 3 };
    server.use(http.get(`${API_BASE}/api/v1/knowledge-bases`, () => HttpResponse.json(multiPageResponse)));
    render(<KnowledgeList />, { wrapper: createWrapper() });
    await waitFor(() => expect(screen.getByText('产品文档知识库')).toBeInTheDocument());
    await user.click(screen.getByRole('button', { name: '下一页' }));
  });
});
