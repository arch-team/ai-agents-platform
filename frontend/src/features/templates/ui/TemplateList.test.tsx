import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { PageResponse } from '@/shared/types';

import { server } from '../../../../tests/mocks/server';

import type { Template } from '../api/types';

import { TemplateList } from './TemplateList';

const API_BASE = 'http://localhost:8000';

// 测试数据
const mockTemplates: Template[] = [
  {
    id: 1,
    name: '客服助手模板',
    description: '适用于客服场景的 Agent 模板',
    category: 'customer_service',
    status: 'draft',
    creator_id: 1,
    system_prompt: '你是客服助手',
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
  },
  {
    id: 2,
    name: '数据分析模板',
    description: '数据分析专用模板',
    category: 'data_analysis',
    status: 'published',
    creator_id: 1,
    system_prompt: '你是数据分析师',
    model_id: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
    temperature: 0.3,
    max_tokens: 8192,
    tool_ids: [],
    knowledge_base_ids: [],
    tags: [],
    usage_count: 25,
    is_featured: false,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

const mockResponse: PageResponse<Template> = {
  items: mockTemplates,
  total: 2,
  page: 1,
  page_size: 12,
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

describe('TemplateList', () => {
  beforeEach(() => {
    server.use(http.get(`${API_BASE}/api/v1/templates`, () => HttpResponse.json(mockResponse)));
  });

  it('应显示加载状态', () => {
    render(<TemplateList />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示模板列表', async () => {
    render(<TemplateList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('客服助手模板')).toBeInTheDocument();
    });
    expect(screen.getByText('数据分析模板')).toBeInTheDocument();
    expect(screen.getByText('使用 10 次')).toBeInTheDocument();
    expect(screen.getByText('使用 25 次')).toBeInTheDocument();
  });

  it('应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/templates`, () =>
        HttpResponse.json({
          items: [],
          total: 0,
          page: 1,
          page_size: 12,
          total_pages: 0,
        }),
      ),
    );

    render(<TemplateList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('暂无模板')).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/templates`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<TemplateList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('点击模板应调用 onSelect', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();

    render(<TemplateList onSelect={handleSelect} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('客服助手模板')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /查看模板: 客服助手模板/ }));
    expect(handleSelect).toHaveBeenCalledWith(1);
  });

  it('应在 onCreate 传入时显示创建按钮', async () => {
    const handleCreate = vi.fn();
    const user = userEvent.setup();

    render(<TemplateList onCreate={handleCreate} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('客服助手模板')).toBeInTheDocument();
    });

    const createButton = screen.getByRole('button', { name: '创建模板' });
    expect(createButton).toBeInTheDocument();
    await user.click(createButton);
    expect(handleCreate).toHaveBeenCalled();
  });

  it('草稿模板应显示发布按钮', async () => {
    render(<TemplateList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('客服助手模板')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '发布 客服助手模板' })).toBeInTheDocument();
  });

  it('已发布模板应显示归档按钮', async () => {
    render(<TemplateList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('数据分析模板')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '归档 数据分析模板' })).toBeInTheDocument();
  });

  it('所有模板应显示删除按钮', async () => {
    render(<TemplateList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('客服助手模板')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '删除 客服助手模板' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '删除 数据分析模板' })).toBeInTheDocument();
  });

  it('应显示分类筛选', async () => {
    render(<TemplateList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('客服助手模板')).toBeInTheDocument();
    });

    expect(screen.getByRole('group', { name: '分类筛选' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '全部' })).toBeInTheDocument();
  });

  it('应显示状态筛选下拉', async () => {
    render(<TemplateList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('客服助手模板')).toBeInTheDocument();
    });

    const filter = screen.getByLabelText('状态');
    expect(filter).toBeInTheDocument();
    expect(filter).toHaveValue('');
  });
});
