import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { Agent } from '@/entities/agent';
import type { PageResponse } from '@/shared/types';

import { server } from '../../../../tests/mocks/server';

import { AgentList } from './AgentList';

const API_BASE = 'http://localhost:8000';

// 测试数据
const mockAgents: Agent[] = [
  {
    id: 1,
    name: '测试 Agent 1',
    description: '第一个测试 Agent',
    system_prompt: '你是助手',
    status: 'draft',
    owner_id: 1,
    config: {
      model_id: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
      temperature: 0.7,
      max_tokens: 4096,
      top_p: 1,
      enable_memory: false,
    },
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: '测试 Agent 2',
    description: '第二个测试 Agent',
    system_prompt: '你是专家',
    status: 'active',
    owner_id: 1,
    config: {
      model_id: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
      temperature: 0.5,
      max_tokens: 2048,
      top_p: 1,
      enable_memory: false,
    },
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

const mockResponse: PageResponse<Agent> = {
  items: mockAgents,
  total: 2,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

// 测试用的 wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('AgentList', () => {
  // 每个测试前注册处理器（使用全局 server）
  beforeEach(() => {
    server.use(http.get(`${API_BASE}/api/v1/agents`, () => HttpResponse.json(mockResponse)));
  });

  it('应显示加载状态', () => {
    render(<AgentList />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示 Agent 列表', async () => {
    render(<AgentList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('测试 Agent 1')).toBeInTheDocument();
    });
    expect(screen.getByText('测试 Agent 2')).toBeInTheDocument();
  });

  it('应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/agents`, () =>
        HttpResponse.json({
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
          total_pages: 0,
        }),
      ),
    );

    render(<AgentList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('暂无 Agent')).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/agents`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<AgentList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('点击 Agent 应调用 onSelect', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();

    render(<AgentList onSelect={handleSelect} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('测试 Agent 1')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /查看 Agent: 测试 Agent 1/ }));
    expect(handleSelect).toHaveBeenCalledWith(1);
  });

  it('应显示状态筛选下拉', async () => {
    render(<AgentList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('测试 Agent 1')).toBeInTheDocument();
    });

    const filter = screen.getByLabelText('状态筛选');
    expect(filter).toBeInTheDocument();
    expect(filter).toHaveValue('');
  });

  it('应在 onCreate 传入时显示创建按钮', async () => {
    const handleCreate = vi.fn();
    const user = userEvent.setup();

    render(<AgentList onCreate={handleCreate} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('测试 Agent 1')).toBeInTheDocument();
    });

    const createButton = screen.getByRole('button', { name: '创建 Agent' });
    expect(createButton).toBeInTheDocument();
    await user.click(createButton);
    expect(handleCreate).toHaveBeenCalled();
  });

  it('草稿状态 Agent 应显示编辑和激活按钮', async () => {
    render(<AgentList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('测试 Agent 1')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '编辑 测试 Agent 1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '激活 测试 Agent 1' })).toBeInTheDocument();
  });

  it('激活状态 Agent 应显示归档按钮', async () => {
    render(<AgentList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('测试 Agent 2')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '归档 测试 Agent 2' })).toBeInTheDocument();
  });
});
