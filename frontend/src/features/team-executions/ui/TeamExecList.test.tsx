import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { PageResponse } from '@/shared/types';

import { server } from '../../../../tests/mocks/server';

import type { TeamExecution } from '../api/types';

import { TeamExecList } from './TeamExecList';

const API_BASE = 'http://localhost:8000';

// 测试数据
const mockExecutions: TeamExecution[] = [
  {
    id: 1,
    agent_id: 1,
    user_id: 1,
    prompt: '分析最近一个月的销售数据',
    status: 'completed',
    result: '分析完成',
    error_message: null,
    conversation_id: null,
    input_tokens: null,
    output_tokens: null,
    started_at: null,
    completed_at: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T01:00:00Z',
  },
  {
    id: 2,
    agent_id: 1,
    user_id: 1,
    prompt: '生成季度报告摘要',
    status: 'running',
    result: null,
    error_message: null,
    conversation_id: null,
    input_tokens: null,
    output_tokens: null,
    started_at: null,
    completed_at: null,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

const mockResponse: PageResponse<TeamExecution> = {
  items: mockExecutions,
  total: 2,
  page: 1,
  page_size: 20,
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

describe('TeamExecList', () => {
  beforeEach(() => {
    server.use(
      http.get(`${API_BASE}/api/v1/team-executions`, () => HttpResponse.json(mockResponse)),
    );
  });

  it('应显示加载状态', () => {
    render(<TeamExecList selectedId={null} onSelect={vi.fn()} />, {
      wrapper: createWrapper(),
    });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示执行列表', async () => {
    render(<TeamExecList selectedId={null} onSelect={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByText('分析最近一个月的销售数据')).toBeInTheDocument();
    });
    expect(screen.getByText('生成季度报告摘要')).toBeInTheDocument();
  });

  it('应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/team-executions`, () =>
        HttpResponse.json({
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0,
        }),
      ),
    );

    render(<TeamExecList selectedId={null} onSelect={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByText(/暂无执行记录/)).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/team-executions`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<TeamExecList selectedId={null} onSelect={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('点击执行项应调用 onSelect', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();

    render(<TeamExecList selectedId={null} onSelect={handleSelect} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByText('分析最近一个月的销售数据')).toBeInTheDocument();
    });

    // TeamExecList 中的按钮没有 aria-label，通过文本查找
    const buttons = screen.getAllByRole('button');
    await user.click(buttons[0]);
    expect(handleSelect).toHaveBeenCalledWith(mockExecutions[0]);
  });

  it('选中项应高亮显示', async () => {
    render(<TeamExecList selectedId={1} onSelect={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByText('分析最近一个月的销售数据')).toBeInTheDocument();
    });

    // 选中项应有 aria-current 属性
    const selectedButton = screen.getByText('分析最近一个月的销售数据').closest('button');
    expect(selectedButton).toHaveAttribute('aria-current', 'true');
  });

  it('应渲染执行列表的 role=list', async () => {
    render(<TeamExecList selectedId={null} onSelect={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByText('分析最近一个月的销售数据')).toBeInTheDocument();
    });

    expect(screen.getByRole('list', { name: '执行列表' })).toBeInTheDocument();
  });
});
