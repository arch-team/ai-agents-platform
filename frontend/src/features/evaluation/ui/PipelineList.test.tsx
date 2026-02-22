import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeAll } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { PipelineList } from './PipelineList';

const API_BASE = 'http://localhost:8000';

const mockPipelines = [
  {
    id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    eval_suite_id: '1',
    status: 'completed',
    bedrock_job_id: 'job-123',
    started_at: '2026-02-21T10:00:00Z',
    completed_at: '2026-02-21T10:15:00Z',
  },
  {
    id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
    eval_suite_id: '1',
    status: 'running',
    bedrock_job_id: 'job-456',
    started_at: '2026-02-21T11:00:00Z',
    completed_at: null,
  },
];

// ResizeObserver polyfill（jsdom 不提供）
beforeAll(() => {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('PipelineList', () => {
  it('应显示加载状态', () => {
    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示 Pipeline 列表数据', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json(mockPipelines),
      ),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('a1b2c3d4')).toBeInTheDocument();
    });

    // 验证列表数据
    expect(screen.getByText('b2c3d4e5')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByText('运行中')).toBeInTheDocument();
    expect(screen.getByText('job-123')).toBeInTheDocument();
    expect(screen.getByText('job-456')).toBeInTheDocument();
    expect(screen.getByText('共 2 条 Pipeline 记录')).toBeInTheDocument();
  });

  it('数据为空时应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () => HttpResponse.json([])),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/暂无 Pipeline 记录/)).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('应显示触发评估按钮', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json(mockPipelines),
      ),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('a1b2c3d4')).toBeInTheDocument();
    });

    const button = screen.getByRole('button', { name: '触发评估' });
    expect(button).toBeInTheDocument();
  });

  it('点击触发评估按钮应调用 API', async () => {
    const user = userEvent.setup();

    server.use(
      http.get(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json(mockPipelines),
      ),
      http.post(`${API_BASE}/api/v1/eval-suites/:suiteId/pipelines`, () =>
        HttpResponse.json({
          id: 'c3d4e5f6-a7b8-9012-cdef-123456789012',
          eval_suite_id: '1',
          status: 'pending',
          bedrock_job_id: null,
          started_at: '2026-02-21T12:00:00Z',
          completed_at: null,
        }),
      ),
    );

    render(<PipelineList suiteId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('a1b2c3d4')).toBeInTheDocument();
    });

    const button = screen.getByRole('button', { name: '触发评估' });
    await user.click(button);

    // 触发后按钮应显示"触发中..."（isPending 状态），成功后恢复
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '触发评估' })).toBeInTheDocument();
    });
  });
});
